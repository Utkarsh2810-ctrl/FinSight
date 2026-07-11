"""
api/routes/qa.py
----------------
POST /api/qa      — full RAG answer (retrieve + generate)
POST /api/retrieve — retrieval only (no generation), useful for debugging
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class QARequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    document_id: Optional[str] = Field(
        default=None,
        description="Restrict retrieval to a single document. Omit to search all."
    )
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    rerank_top_n: Optional[int] = Field(default=None, ge=1, le=20)
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Prior turns: [{'role': 'user'|'assistant', 'content': '...'}]"
    )


class SourceChunk(BaseModel):
    chunk_id: str
    company: Optional[str]
    year: Optional[Any]
    quarter: Optional[str]
    page: Optional[Any]
    chunk_type: Optional[str]
    rerank_score: Optional[float]
    text_preview: str


class QAResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    latency_ms: int
    model: str
    query: str


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3)
    document_id: Optional[str] = None
    top_k: Optional[int] = None
    rerank_top_n: Optional[int] = None


class RetrieveResponse(BaseModel):
    query: str
    chunks: List[Dict[str, Any]]
    n_chunks: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/qa", response_model=QAResponse)
async def answer_question(body: QARequest, request: Request):
    """
    Full RAG pipeline: retrieve relevant chunks then generate a grounded answer.

    If document_id is provided, restricts retrieval to that document.
    If omitted, searches across all indexed documents (useful for cross-doc questions).
    """
    retriever = request.app.state.retriever
    qa_pipeline = request.app.state.qa_pipeline
    document_store = request.app.state.document_store

    # Validate document_id if provided
    if body.document_id and body.document_id not in document_store:
        raise HTTPException(
            status_code=404,
            detail=f"document_id '{body.document_id}' not found. Upload the document first."
        )

    # Retrieve
    try:
        chunks = retriever.retrieve(
            query=body.query,
            document_id=body.document_id,
            top_k=body.top_k,
            rerank_top_n=body.rerank_top_n,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant chunks found. Make sure a document has been uploaded and indexed."
        )

    # Generate
    try:
        result = qa_pipeline.answer(
            query=body.query,
            chunks=chunks,
            conversation_history=body.conversation_history,
        )
    except Exception as e:
        logger.error(f"QA generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Answer generation error: {str(e)}")

    return QAResponse(**result)


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_chunks(body: RetrieveRequest, request: Request):
    """
    Retrieval only — returns the top reranked chunks without generating an answer.
    Useful for debugging retrieval quality and inspecting rerank scores.
    """
    retriever = request.app.state.retriever

    try:
        chunks = retriever.retrieve(
            query=body.query,
            document_id=body.document_id,
            top_k=body.top_k,
            rerank_top_n=body.rerank_top_n,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    return RetrieveResponse(query=body.query, chunks=chunks, n_chunks=len(chunks))
