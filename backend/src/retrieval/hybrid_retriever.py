"""
hybrid_retriever.py
-------------------
Layer 2 — Hybrid Retrieval.

Pipeline per query:
    query → dense_search (ChromaDB + sentence-transformers)
          → sparse_search (BM25Okapi)
          → reciprocal_rank_fusion (RRF)
          → rerank (CrossEncoder)
          → top-n chunks returned to QA layer

Design decisions:
    - One shared ChromaDB collection; documents filtered by document_id in metadata.
    - Per-document BM25 index stored in memory (dict keyed by document_id).
    - RRF is rank-based, not score-based, because cosine similarity and BM25
      scores have incomparable distributions. Ranks are always 1..N.
    - CrossEncoder scores (query, chunk) pairs jointly — much more accurate than
      bi-encoder for reranking, but too slow for first-stage retrieval.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from loguru import logger
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder


class HybridRetriever:
    """
    Manages indexing and retrieval for all ingested documents.

    Attributes:
        _bm25_store : maps document_id → (BM25Okapi index, ordered chunk list)
        _collection : shared ChromaDB collection (all documents, filtered by metadata)
        _cross_encoder : CrossEncoder model for reranking
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._cfg = config["retrieval"]

        # --- Dense retrieval: ChromaDB ---
        embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=self._cfg["embedding_model"]
        )
        client = chromadb.PersistentClient(path=self._cfg["chroma_persist_dir"])
        self._collection = client.get_or_create_collection(
            name=self._cfg["chroma_collection"],
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB collection '{self._cfg['chroma_collection']}' "
            f"loaded ({self._collection.count()} existing chunks)"
        )

        # --- Sparse retrieval: per-document BM25 ---
        # dict: document_id -> (BM25Okapi, List[chunk_dict])
        self._bm25_store: Dict[str, Tuple[BM25Okapi, List[Dict]]] = {}

        # --- Reranking: CrossEncoder ---
        self._cross_encoder = CrossEncoder(self._cfg["reranker_model"])
        logger.info(f"CrossEncoder loaded: {self._cfg['reranker_model']}")

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_document(self, document_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Indexes all chunks for a document into both ChromaDB and BM25.

        Args:
            document_id : UUID that identifies the document
            chunks      : output of parser.ingest()
        """
        if not chunks:
            logger.warning(f"No chunks to index for document_id={document_id}")
            return

        # --- ChromaDB dense index ---
        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c["document_id"],
                "company": c["company"],
                "year": str(c["year"]),
                "quarter": c["quarter"],
                "page": str(c["page"]),
                "chunk_type": c["chunk_type"],
            }
            for c in chunks
        ]

        # ChromaDB upsert handles duplicate chunk_ids gracefully
        self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Indexed {len(chunks)} chunks into ChromaDB for document_id={document_id}")

        # --- BM25 sparse index ---
        tokenized = [c["text"].lower().split() for c in chunks]
        self._bm25_store[document_id] = (BM25Okapi(tokenized), chunks)
        logger.info(f"BM25 index built for document_id={document_id} ({len(chunks)} chunks)")

    def delete_document(self, document_id: str) -> None:
        """
        Deletes all chunks for a document from ChromaDB and BM25 store.
        """
        try:
            self._collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted ChromaDB chunks for document_id={document_id}")
        except Exception as e:
            logger.error(f"Error deleting ChromaDB chunks for document_id={document_id}: {e}")

        if document_id in self._bm25_store:
            del self._bm25_store[document_id]
            logger.info(f"Deleted BM25 index for document_id={document_id}")

    # ------------------------------------------------------------------
    # Dense retrieval
    # ------------------------------------------------------------------

    def _dense_search(
        self,
        query: str,
        document_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for the top-k semantically similar chunks.

        Args:
            document_id : if provided, restricts retrieval to that document only.
                          Pass None to search across all indexed documents.
        """
        where_filter = {"document_id": document_id} if document_id else None

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i, (doc, meta, dist) in enumerate(
            zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
        ):
            chunks.append(
                {
                    "chunk_id": results["ids"][0][i],
                    "text": doc,
                    "dense_score": float(1 - dist),  # cosine distance → similarity
                    "dense_rank": i + 1,
                    **meta,
                }
            )

        logger.debug(f"Dense search returned {len(chunks)} candidates")
        return chunks

    # ------------------------------------------------------------------
    # Sparse retrieval
    # ------------------------------------------------------------------

    def _sparse_search(
        self,
        query: str,
        document_id: Optional[str],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        BM25 retrieval. Searches within document_id's index if provided,
        otherwise merges results across all document BM25 indices.
        """
        query_tokens = query.lower().split()

        if document_id:
            if document_id not in self._bm25_store:
                logger.warning(f"No BM25 index found for document_id={document_id}")
                return []
            bm25, chunk_list = self._bm25_store[document_id]
            scores = bm25.get_scores(query_tokens)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            top_indices = ranked_indices[:top_k]
            return [
                {**chunk_list[i], "sparse_score": float(scores[i]), "sparse_rank": rank + 1}
                for rank, i in enumerate(top_indices)
            ]

        # Cross-document BM25: score across all, merge by top score
        all_candidates = []
        for doc_id, (bm25, chunk_list) in self._bm25_store.items():
            scores = bm25.get_scores(query_tokens)
            for i, score in enumerate(scores):
                all_candidates.append((score, chunk_list[i]))

        all_candidates.sort(key=lambda x: x[0], reverse=True)
        return [
            {**chunk, "sparse_score": float(score), "sparse_rank": rank + 1}
            for rank, (score, chunk) in enumerate(all_candidates[:top_k])
        ]

    # ------------------------------------------------------------------
    # RRF Fusion  (✍️ core algorithm — understand this before interviews)
    # ------------------------------------------------------------------

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Merges two ranked lists using Reciprocal Rank Fusion.

        Formula: rrf_score(doc) = Σ  1 / (k + rank_i(doc))
                                  i ∈ {dense, sparse}

        Why ranks, not scores:
            Cosine similarity and BM25 scores live on incomparable scales.
            A cosine similarity of 0.85 and a BM25 score of 12.4 cannot be
            meaningfully averaged. Ranks are always 1..N regardless of the
            underlying scoring function — RRF is therefore scale-invariant.

        Why k=60:
            Proposed in Cormack et al. (2009). Small k amplifies differences
            between the very top ranks. k=60 provides a robust damping factor
            that works well across diverse IR tasks without tuning.
        """
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict] = {}

        for rank, doc in enumerate(dense_results, start=1):
            cid = doc["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            doc_map[cid] = doc

        for rank, doc in enumerate(sparse_results, start=1):
            cid = doc["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
            if cid not in doc_map:
                doc_map[cid] = doc

        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

        fused = []
        for cid in sorted_ids:
            entry = doc_map[cid].copy()
            entry["rrf_score"] = scores[cid]
            fused.append(entry)

        logger.debug(f"RRF merged {len(dense_results)} dense + {len(sparse_results)} sparse → {len(fused)} candidates")
        return fused

    # ------------------------------------------------------------------
    # CrossEncoder Reranking
    # ------------------------------------------------------------------

    def _rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int,
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidates using a CrossEncoder.

        Why CrossEncoder here and not as the first-stage retriever:
            CrossEncoder encodes (query, document) jointly — far more accurate
            than bi-encoder similarity, but O(n) inference per query-doc pair.
            At first-stage scale (thousands of chunks) this is too slow.
            At reranking scale (20-50 candidates) it's fast and accurate.
        """
        if not candidates:
            return []

        pairs = [(query, c["text"]) for c in candidates]
        scores = self._cross_encoder.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        top = reranked[:top_n]

        logger.debug(f"CrossEncoder reranked {len(candidates)} → {len(top)} final chunks")
        return top

    # ------------------------------------------------------------------
    # Public retrieval interface
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        rerank_top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Full retrieval pipeline: dense → sparse → RRF → rerank.

        Args:
            query        : natural language question
            document_id  : restrict to a single document (None = all documents)
            top_k        : candidates from each retriever (defaults to config)
            rerank_top_n : final chunks after reranking (defaults to config)

        Returns:
            Ordered list of ChunkDicts with dense_score, sparse_score,
            rrf_score, and rerank_score fields added.
        """
        k = top_k or self._cfg["top_k"]
        n = rerank_top_n or self._cfg["rerank_top_n"]
        rrf_k = self._cfg.get("rrf_k", 60)

        dense = self._dense_search(query, document_id, k)
        sparse = self._sparse_search(query, document_id, k)
        fused = self._reciprocal_rank_fusion(dense, sparse, k=rrf_k)
        final = self._rerank(query, fused, top_n=n)

        return final
