"""
pipeline.py
-----------
Layer 3 — Question Answering.

Takes reranked chunks from the retrieval layer, assembles them into a
structured context string with source labels, and sends to Groq with a
finance-specific system prompt.

Design decisions:
    - System prompt restricts the LLM to ONLY the provided context.
      Prevents hallucination of specific financial figures.
    - Source labels [Company | Period | Page | Type] make every claim
      traceable to a specific document location.
    - Temperature = 0.1 for factual consistency.
    - LangChain is used only for conversational memory (optional).
      The core call goes directly to the Groq SDK for simplicity.
"""

import os
import time
from typing import Any, Dict, List, Optional

from groq import Groq
from loguru import logger

# ✍️  Finance system prompt — the most impactful prompt engineering in the system.
#     Every sentence is intentional. Modify this if retrieval quality is good
#     but answers are unfaithful or vague.
FINANCE_SYSTEM_PROMPT = """You are FinSight, a precise financial document analyst.

Your ONLY information source is the context provided below, extracted from financial filings and earnings reports. You have no access to external knowledge, market data, or information beyond what appears in the context.

STRICT RULES:
1. Base every statement EXCLUSIVELY on the provided context. Do not use training knowledge about companies, markets, or financial events.
2. When citing a specific figure, metric, or claim, reference its source using this format: [Company | Period | Page | Type]
3. Report financial figures exactly as stated in the source — preserve units (USD millions, USD billions, %) without conversion unless explicitly requested.
4. If the context does not contain enough information to answer, respond with: "The provided document does not contain sufficient information to answer this question." Do not guess, infer, or approximate.
5. For comparison questions, clearly note when data for only one side of the comparison is available in the context.
6. Structure your response: lead with the direct answer, follow with supporting evidence and citations.
7. Do not speculate about causes, future performance, or implications beyond what the document explicitly states.

CONTEXT (retrieved from financial documents):
{context}"""


class QAPipeline:
    """
    Orchestrates context assembly and LLM-based question answering.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._cfg = config["qa"]

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not set in environment. QAPipeline initialized in retrieval-fallback mode.")
            self._client = None
        else:
            self._client = Groq(api_key=api_key)
            logger.info(f"QAPipeline initialised with model: {self._cfg['groq_model']}")


    # ------------------------------------------------------------------
    # Context assembly  (✍️ write this yourself — it encodes your schema)
    # ------------------------------------------------------------------

    def assemble_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats reranked chunks into a single context string for the LLM.

        Each chunk is prefixed with a source label so the LLM can cite it:
            [Apple | Q3 2024 | Page 7 | table]
            ... chunk text ...

        The rerank_score is included so the prompt reflects confidence ordering.
        """
        if not chunks:
            return "No relevant context found in the indexed documents."

        parts = []
        for i, chunk in enumerate(chunks, start=1):
            label = (
                f"[{chunk.get('company', 'Unknown')} | "
                f"{chunk.get('quarter', '')} {chunk.get('year', '')} | "
                f"Page {chunk.get('page', '?')} | "
                f"{chunk.get('chunk_type', 'text')}]"
            )
            score_line = f"(relevance: {chunk.get('rerank_score', 0.0):.3f})"
            parts.append(f"--- Source {i} {score_line}\n{label}\n{chunk['text']}")

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Answer generation
    # ------------------------------------------------------------------

    def answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a grounded answer using the Groq LLM.

        Args:
            query                : the user's natural language question
            chunks               : reranked chunks from HybridRetriever.retrieve()
            conversation_history : optional prior turns for conversational memory
                                   format: [{"role": "user"|"assistant", "content": str}]

        Returns:
            {
                "answer"      : str,
                "sources"     : List[Dict] — the chunks used as context,
                "latency_ms"  : int,
                "model"       : str,
                "query"       : str,
            }
        """
        context = self.assemble_context(chunks)
        system_prompt = FINANCE_SYSTEM_PROMPT.format(context=context)

        # Build messages array — supports multi-turn if history is provided
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})

        # Strip heavy text from sources before returning to keep API response small
        sources = [
            {
                "chunk_id": c["chunk_id"],
                "company": c.get("company"),
                "year": c.get("year"),
                "quarter": c.get("quarter"),
                "page": c.get("page"),
                "chunk_type": c.get("chunk_type"),
                "rerank_score": c.get("rerank_score"),
                "text_preview": c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"],
            }
            for c in chunks
        ]

        if not self._client:
            answer_text = (
                "GROQ_API_KEY is not configured in the backend environment. "
                "Here are the grounded document excerpts retrieved for your query:\n\n" + context
            )
            return {
                "answer": answer_text,
                "sources": sources,
                "latency_ms": 0,
                "model": "retrieval-fallback",
                "query": query,
            }

        t0 = time.monotonic()

        response = self._client.chat.completions.create(
            model=self._cfg["groq_model"],
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=self._cfg["max_tokens"],
            temperature=self._cfg["temperature"],
        )
        answer_text = response.choices[0].message.content.strip()
        latency_ms = int((time.monotonic() - t0) * 1000)

        return {
            "answer": answer_text,
            "sources": sources,
            "latency_ms": latency_ms,
            "model": self._cfg["groq_model"],
            "query": query,
        }
