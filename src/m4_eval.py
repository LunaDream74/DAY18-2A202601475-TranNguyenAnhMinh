from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY, TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    lengths = {len(questions), len(answers), len(contexts), len(ground_truths)}
    if len(lengths) != 1:
        raise ValueError("RAGAS input lists must have equal lengths")

    metric_names = (
        "faithfulness", "answer_relevancy", "context_precision", "context_recall"
    )
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )
        frame = result.to_pandas()
        per_question = [
            EvalResult(
                question=row["question"],
                answer=row["answer"],
                contexts=list(row["contexts"]),
                ground_truth=row["ground_truth"],
                **{name: float(row.get(name, 0.0)) for name in metric_names},
            )
            for _, row in frame.iterrows()
        ]
        return {
            **{name: float(frame[name].fillna(0.0).mean()) for name in metric_names},
            "per_question": per_question,
        }
    except Exception as error:
        print(f"  ⚠️  RAGAS evaluation failed: {error}")
        per_question = [
            EvalResult(question, answer, context, truth, 0.0, 0.0, 0.0, 0.0)
            for question, answer, context, truth
            in zip(questions, answers, contexts, ground_truths)
        ]
        return {**{name: 0.0 for name in metric_names}, "per_question": per_question}


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten the prompt and lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25 retrieval"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filters"),
        "answer_relevancy": ("Answer does not match the question", "Improve the answer prompt"),
    }
    analyzed = []
    for result in eval_results:
        scores = {name: float(getattr(result, name)) for name in diagnostic_tree}
        worst_metric = min(scores, key=scores.get)
        diagnosis, suggested_fix = diagnostic_tree[worst_metric]
        analyzed.append({
            "question": result.question,
            "average_score": sum(scores.values()) / len(scores),
            "worst_metric": worst_metric,
            "score": scores[worst_metric],
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
        })
    analyzed.sort(key=lambda item: item["average_score"])
    return analyzed[:max(bottom_n, 0)]


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
