"""
api/routes/eval.py
------------------
POST /api/evaluate — runs RAGAS evaluation over an uploaded benchmark JSON.

Retrieval + generation reuses the app's existing retriever/qa_pipeline
(same as the QA flow). Scoring calls ragas.evaluate() directly in-process.

Benchmark file format: JSON array of objects with fields:
    question    : str
    ground_truth: str
    document_id : str  (must match an already-indexed document)
"""

import json
import os
import time
from typing import List

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from loguru import logger
from pydantic import BaseModel

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PerQuestionScore(BaseModel):
    question: str
    answer: str
    ground_truth: str
    faithfulness: float
    context_precision: float
    context_recall: float


class EvaluationResponse(BaseModel):
    faithfulness: float
    context_precision: float
    context_recall: float
    n_questions: int
    per_question: List[PerQuestionScore]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Benchmark file must be a .json file.")

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
        raise HTTPException(status_code=422, detail="Benchmark has more than 100 entries. Limit to 100.")

    for i, entry in enumerate(benchmark):
        missing = [k for k in ("question", "ground_truth", "document_id") if k not in entry]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Entry {i} is missing required field(s): {missing}",
            )

    retriever = request.app.state.retriever
    qa_pipeline = request.app.state.qa_pipeline

    # --- Step 1: retrieval + generation, reusing the app's existing pipeline ---
    records = []
    skipped = []
    for entry in benchmark:
        try:
            chunks = retriever.retrieve(entry["question"], document_id=entry["document_id"])
            if not chunks:
                skipped.append({"question": entry["question"], "reason": "No chunks retrieved for document_id"})
                continue
            result = qa_pipeline.answer(entry["question"], chunks)
            records.append({
                "question": entry["question"],
                "answer": result["answer"],
                "contexts": [c["text"] for c in chunks],
                "ground_truth": entry["ground_truth"],
            })
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Skipping question '{entry['question']}' due to error: {e}")
            skipped.append({"question": entry["question"], "reason": str(e)})

    if not records:
        raise HTTPException(
            status_code=500,
            detail=f"No questions could be answered. Skipped: {skipped}",
        )

    logger.info(f"RAGAS evaluation: {len(records)} answered, {len(skipped)} skipped")

    # --- Step 2: run RAGAS scoring directly in-process ---
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in this process's environment.")

    try:
        from langchain_openai import ChatOpenAI
        from ragas import EvaluationDataset, SingleTurnSample
        from ragas import evaluate as ragas_evaluate
        from ragas.llms import LangchainLLMWrapper

        chat_model = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0,
        )
        evaluator_llm = LangchainLLMWrapper(chat_model)

        # Metric imports: try lowercase singletons first (ragas 0.1–0.3),
        # fall back to PascalCase classes (ragas 0.4+).
        try:
            from ragas.metrics import context_precision, context_recall, faithfulness
            metrics = [faithfulness, context_precision, context_recall]
        except ImportError:
            from ragas.metrics import ContextPrecision, ContextRecall, Faithfulness
            metrics = [Faithfulness(), ContextPrecision(), ContextRecall()]

        samples = [
            SingleTurnSample(
                user_input=r["question"],
                response=r["answer"],
                retrieved_contexts=r["contexts"],
                reference=r["ground_truth"],
            )
            for r in records
        ]
        dataset = EvaluationDataset(samples=samples)

        logger.info("Running RAGAS evaluation (direct in-process)...")
        ragas_result = ragas_evaluate(dataset=dataset, metrics=metrics, llm=evaluator_llm)
        df = ragas_result.to_pandas()
        logger.info("RAGAS evaluation complete.")

    except Exception as e:
        logger.error(f"RAGAS scoring failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAGAS scoring failed: {type(e).__name__}: {e}",
        )

    # --- Step 3: assemble response ---
    def col(name: str, row) -> float:
        val = row.get(name, None)
        return float(val) if val is not None else 0.0

    per_question = []
    for i, r in enumerate(records):
        row = df.iloc[i]
        per_question.append({
            "question": r["question"],
            "answer": r["answer"],
            "ground_truth": r["ground_truth"],
            "faithfulness": col("faithfulness", row),
            "context_precision": col("context_precision", row),
            "context_recall": col("context_recall", row),
        })

    return EvaluationResponse(
        faithfulness=float(df["faithfulness"].mean()) if "faithfulness" in df else 0.0,
        context_precision=float(df["context_precision"].mean()) if "context_precision" in df else 0.0,
        context_recall=float(df["context_recall"].mean()) if "context_recall" in df else 0.0,
        n_questions=len(records),
        per_question=per_question,
    )