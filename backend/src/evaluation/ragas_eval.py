"""
ragas_eval.py
-------------
Layer 5 — RAGAS Evaluation.

Measures RAG system quality across 4 dimensions:

    faithfulness      : Are answer claims supported by the retrieved context?
                        (NLI-based — model checks entailment between claim and source)
    answer_relevancy  : Does the answer actually address the question asked?
                        (Embedding similarity between question and answer)
    context_precision : Of the retrieved chunks, what fraction were actually useful?
                        (Precision of retrieval w.r.t. ground truth)
    context_recall    : Were all necessary chunks retrieved?
                        (Recall of retrieval w.r.t. ground truth)

Benchmark format (benchmark.json):
    [
      {
        "question": "What was Apple's Q3 2024 revenue?",
        "ground_truth": "Apple reported revenue of $85.8 billion in Q3 2024.",
        "document_id": "uuid-of-the-indexed-document"
      },
      ...
    ]

The evaluation module runs the full pipeline for each benchmark question,
collects (question, answer, contexts, ground_truth) tuples, then passes them
to RAGAS for scoring.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from datasets import Dataset
from langchain_groq import ChatGroq
from loguru import logger
from ragas import evaluate
from ragas.llms import LangchainLLM
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)


def load_benchmark(benchmark_path: str) -> List[Dict[str, Any]]:
    """
    Loads and validates the benchmark JSON file.

    Required fields per entry: question, ground_truth, document_id.
    Entries missing required fields are skipped with a warning.
    """
    path = Path(benchmark_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")

    with open(path, "r") as f:
        data = json.load(f)

    valid = []
    for i, entry in enumerate(data):
        if not all(k in entry for k in ("question", "ground_truth", "document_id")):
            logger.warning(f"Benchmark entry {i} missing required fields — skipping")
            continue
        valid.append(entry)

    logger.info(f"Loaded {len(valid)} valid benchmark entries from {benchmark_path}")
    return valid


def _build_ragas_dataset(
    benchmark: List[Dict[str, Any]],
    retriever,
    qa_pipeline,
) -> Dict[str, List]:
    """
    Runs the full RAG pipeline for each benchmark question and collects
    the (question, answer, contexts, ground_truth) tuples RAGAS expects.

    Args:
        benchmark   : list of benchmark dicts
        retriever   : HybridRetriever instance
        qa_pipeline : QAPipeline instance
    """
    questions, answers, contexts_list, ground_truths = [], [], [], []

    for i, entry in enumerate(benchmark):
        question = entry["question"]
        ground_truth = entry["ground_truth"]
        document_id = entry.get("document_id")

        logger.info(f"Evaluating [{i+1}/{len(benchmark)}]: {question[:60]}...")

        try:
            # Retrieve relevant chunks
            chunks = retriever.retrieve(query=question, document_id=document_id)

            # Generate answer
            result = qa_pipeline.answer(query=question, chunks=chunks)

            questions.append(question)
            answers.append(result["answer"])
            # RAGAS expects contexts as a list of strings
            contexts_list.append([c["text"] for c in chunks])
            ground_truths.append(ground_truth)

        except Exception as e:
            logger.error(f"Error on benchmark entry {i}: {e}")
            # Add placeholder so indices stay aligned
            questions.append(question)
            answers.append("ERROR: Pipeline failed")
            contexts_list.append([])
            ground_truths.append(ground_truth)

    return {
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    }


def run_ragas_evaluation(
    benchmark_path: str,
    retriever,
    qa_pipeline,
    use_groq: bool = True,
) -> Dict[str, Any]:
    """
    Runs RAGAS evaluation over the full benchmark.

    Args:
        benchmark_path : path to benchmark.json
        retriever      : HybridRetriever instance
        qa_pipeline    : QAPipeline instance
        use_groq       : if True, use Groq as the judge LLM instead of OpenAI

    Returns:
        {
            "faithfulness"      : float (0-1),
            "answer_relevancy"  : float (0-1),
            "context_precision" : float (0-1),
            "context_recall"    : float (0-1),
            "n_questions"       : int,
            "per_question"      : List[Dict] — per-row scores
        }
    """
    benchmark = load_benchmark(benchmark_path)

    # --- Configure judge LLM ---
    if use_groq:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise EnvironmentError("GROQ_API_KEY not set — required for RAGAS evaluation")

        # RAGAS uses LangChain under the hood; wrap Groq via langchain-groq
        groq_llm = ChatGroq(
            model_name="llama-3.1-8b-instant",
            groq_api_key=groq_api_key,
            temperature=0.0,
        )

        ragas_llm = LangchainLLM(groq_llm)

        for metric in [faithfulness, answer_relevancy, context_precision, context_recall]:
            metric.llm = ragas_llm

        logger.info("RAGAS configured to use Groq (llama3-8b-8192) as judge LLM")
    else:
        # Falls back to RAGAS default (OpenAI GPT-3.5)
        logger.info("RAGAS using default OpenAI judge LLM")

    # --- Build evaluation dataset ---
    ragas_data = _build_ragas_dataset(benchmark, retriever, qa_pipeline)
    dataset = Dataset.from_dict(ragas_data)

    # --- Run evaluation ---
    logger.info("Running RAGAS evaluation...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    scores_df = result.to_pandas()

    # Build per-question breakdown
    per_question = []
    for i, row in scores_df.iterrows():
        per_question.append(
            {
                "question": ragas_data["question"][i],
                "answer": ragas_data["answer"][i],
                "ground_truth": ragas_data["ground_truth"][i],
                "faithfulness": round(float(row.get("faithfulness", 0)), 4),
                "answer_relevancy": round(float(row.get("answer_relevancy", 0)), 4),
                "context_precision": round(float(row.get("context_precision", 0)), 4),
                "context_recall": round(float(row.get("context_recall", 0)), 4),
            }
        )

    # Aggregate means
    aggregate = {
        "faithfulness": round(float(scores_df["faithfulness"].mean()), 4),
        "answer_relevancy": round(float(scores_df["answer_relevancy"].mean()), 4),
        "context_precision": round(float(scores_df["context_precision"].mean()), 4),
        "context_recall": round(float(scores_df["context_recall"].mean()), 4),
        "n_questions": len(benchmark),
        "per_question": per_question,
    }

    logger.info(
        f"RAGAS evaluation complete | "
        f"faithfulness={aggregate['faithfulness']} | "
        f"answer_relevancy={aggregate['answer_relevancy']} | "
        f"context_precision={aggregate['context_precision']} | "
        f"context_recall={aggregate['context_recall']}"
    )

    return aggregate
