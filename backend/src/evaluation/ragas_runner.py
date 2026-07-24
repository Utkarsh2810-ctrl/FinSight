"""
src/evaluation/ragas_runner.py
-------------------------------
Standalone script — runs ONLY under eval_venv (Python 3.13), never imported
by the main FastAPI app. Scores pre-generated Q&A records with RAGAS using
Groq as the judge LLM (via its OpenAI-compatible endpoint).

Usage:
    eval_venv/Scripts/python.exe ragas_runner.py <input_json_path>

Input JSON format (list of objects):
    [
      {"question": str, "answer": str, "contexts": [str, ...], "ground_truth": str},
      ...
    ]

Prints a single JSON object to stdout on success:
    {
      "faithfulness": float, "context_precision": float, "context_recall": float,
      "n_questions": int,
      "per_question": [ {question, answer, ground_truth, faithfulness,
                          context_precision, context_recall}, ... ]
    }

On failure, prints {"error": "<message>"} to stdout and exits non-zero.
All diagnostic/progress output goes to stderr so stdout stays pure JSON.
"""

import json
import os
import sys


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: ragas_runner.py <input_json_path>"}))
        return 1

    input_path = sys.argv[1]

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not isinstance(records, list) or len(records) == 0:
            raise ValueError("Input must be a non-empty JSON array of records.")

        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY not found in subprocess environment.")

        log(f"Loaded {len(records)} records. Configuring Groq judge LLM...")

        from langchain_openai import ChatOpenAI
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.llms import LangchainLLMWrapper

        chat_model = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=0,
        )
        evaluator_llm = LangchainLLMWrapper(chat_model)

        # Metric imports: try the lowercase pre-instantiated singletons first
        # (stable across ragas 0.1.x-0.3.x), fall back to PascalCase classes
        # (ragas 0.4.x's newer collection-based API) if that import fails.
        try:
            from ragas.metrics import context_precision, context_recall, faithfulness
            metrics = [faithfulness, context_precision, context_recall]
            log("Using singleton metric instances (legacy API).")
        except ImportError:
            from ragas.metrics import ContextPrecision, ContextRecall, Faithfulness
            metrics = [Faithfulness(), ContextPrecision(), ContextRecall()]
            log("Using class-based metrics (0.4.x API).")

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

        log("Running RAGAS evaluation (this calls the judge LLM once per metric per question)...")
        result = evaluate(dataset=dataset, metrics=metrics, llm=evaluator_llm)
        df = result.to_pandas()
        log("Evaluation complete. Assembling response...")

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

        output = {
            "faithfulness": float(df["faithfulness"].mean()) if "faithfulness" in df else 0.0,
            "context_precision": float(df["context_precision"].mean()) if "context_precision" in df else 0.0,
            "context_recall": float(df["context_recall"].mean()) if "context_recall" in df else 0.0,
            "n_questions": len(records),
            "per_question": per_question,
        }

        print(json.dumps(output))
        return 0

    except Exception as e:
        log(f"FATAL: {type(e).__name__}: {e}")
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())