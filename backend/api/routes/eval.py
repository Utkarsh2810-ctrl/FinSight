"""
api/routes/eval.py
------------------
POST /api/evaluate — runs RAGAS evaluation over an uploaded benchmark JSON.

The benchmark file must be a JSON array in the format documented in ragas_eval.py.
Results are returned immediately (no async — RAGAS calls the judge LLM per question,
so latency scales linearly with benchmark size).
"""

import asyncio
import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from loguru import logger
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=1)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PerQuestionScore(BaseModel):
    question: str
    answer: str
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


class EvaluationResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    n_questions: int
    per_question: List[PerQuestionScore]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: Request, file: UploadFile = File(...)):
    """
    Run RAGAS evaluation over a benchmark JSON file.

    Expected file format: JSON array of objects with fields:
        question    : str
        ground_truth: str
        document_id : str  (must match an already-indexed document)

    Returns aggregate and per-question RAGAS scores.
    """
    from src.evaluation.ragas_eval import run_ragas_evaluation
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Benchmark file must be a .json file.")

    # Read and validate JSON
    try:
        content = await file.read()
        benchmark = json.loads(content)
        if not isinstance(benchmark, list):
            raise ValueError("Benchmark must be a JSON array.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    if len(benchmark) == 0:
        raise HTTPException(status_code=422, detail="Benchmark file is empty.")

    if len(benchmark) > 100:
        raise HTTPException(
            status_code=422,
            detail="Benchmark has more than 100 entries. Limit to 100 for evaluation."
        )

    # Save to a temp file so ragas_eval can load from disk
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    retriever = request.app.state.retriever
    qa_pipeline = request.app.state.qa_pipeline

    logger.info(f"RAGAS evaluation started: {len(benchmark)} questions")

    loop = asyncio.get_event_loop()
    fn = partial(run_ragas_evaluation, tmp_path, retriever, qa_pipeline)

    try:
        result = await loop.run_in_executor(_executor, fn)
    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return EvaluationResponse(**result)
