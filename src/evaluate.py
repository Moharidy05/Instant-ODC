from __future__ import annotations

import json
from pathlib import Path

from src.answering.answer import full_pipeline
from src.answering.citation_validator import validate_citations
from src.core.config import project_path
from src.retrieval.scoring import average_similarity, precision_at_k
from src.safety.unsupported_claims import find_unsupported_claims


QUERIES_PATH = project_path("data", "evaluation", "test_queries.jsonl")
RETRIEVAL_RESULTS_PATH = project_path("data", "evaluation", "retrieval_results.md")
DAY3_PATH = project_path("data", "evaluation", "day3_generation_eval.md")
DAY4_PATH = project_path("data", "evaluation", "day4_safety_eval.md")


def load_test_queries(path: Path = QUERIES_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _expected_refusal(row: dict) -> bool:
    return "refuse" in row.get("expected_behavior", "")


def _actual_refusal(result: dict) -> bool:
    return result["safety_result"].get("safety_label") == "refuse" or "Food Safety Classification:\nrefused" in result["answer"]


def _has_classification(answer: str) -> bool:
    labels = [
        "encouraged",
        "suitable_with_caution",
        "better_to_limit",
        "not_supported_by_retrieved_evidence",
        "refused",
    ]
    return "Food Safety Classification:" in answer and any(label in answer for label in labels)


def run_evaluation() -> None:
    rows = load_test_queries()
    results = []
    for row in rows:
        print(f"[EVAL] {row['id']} {row['query']}")
        result = full_pipeline(row["query"], disease_layer="diabetes", top_k=5)
        chunks = result["chunks"]
        citation = (
            validate_citations(result["answer"], chunks)
            if chunks
            else {"valid": _actual_refusal(result), "failures": [], "cited_chunk_ids": []}
        )
        unsupported = find_unsupported_claims(result["answer"], chunks) if chunks else []
        results.append(
            {
                "row": row,
                "result": result,
                "citation": citation,
                "unsupported": unsupported,
                "precision_at_5": precision_at_k(chunks, row.get("expected_evidence_topic", row["query"]), 5),
                "avg_score": average_similarity(chunks),
            }
        )
    write_retrieval_results(results)
    write_day3(results)
    write_day4(results)


def write_retrieval_results(results: list[dict]) -> None:
    lines = ["# Retrieval & Answer Evaluation Results", "", f"Total queries evaluated: {len(results)}", ""]
    lines.extend(["| ID | Category | Safety | Chunks | Avg retrieval score | Refusal expected/actual |", "|---|---|---|---:|---:|---|"])
    for item in results:
        row = item["row"]
        result = item["result"]
        lines.append(
            f"| {row['id']} | {row.get('category', '')} | {result['safety_result'].get('safety_label')} | "
            f"{len(result['chunks'])} | {item['avg_score']:.3f} | {_expected_refusal(row)}/{_actual_refusal(result)} |"
        )
    lines.append("")
    for item in results:
        row = item["row"]
        result = item["result"]
        lines.extend([f"## {row['id']} — {row['query']}", "", f"Expected behavior: `{row['expected_behavior']}`", ""])
        lines.extend(["| Rank | Chunk ID | Section | Pages | Similarity |", "|---:|---|---|---|---:|"])
        for idx, chunk in enumerate(result["chunks"], start=1):
            lines.append(
                f"| {idx} | `{chunk.get('chunk_id', '?')}` | {chunk.get('section_title', '?')} | "
                f"{chunk.get('page_start', '?')}-{chunk.get('page_end', '?')} | {float(chunk.get('similarity', 0)):.4f} |"
            )
        lines.extend(["", "### Answer", "", "```text", result["answer"][:2000], "```", ""])
    RETRIEVAL_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {RETRIEVAL_RESULTS_PATH}")


def write_day3(results: list[dict]) -> None:
    lines = [
        "# Day 3 Grounded Generation & Citation Evaluation",
        "",
        "| ID | Has citations | Citation valid | Uses retrieved evidence heuristic | Refusal behavior ok | Has classification |",
        "|---|---|---|---|---|---|",
    ]
    for item in results:
        row = item["row"]
        answer = item["result"]["answer"]
        has_citations = "Citations:" in answer and bool(
            "chunk ID" in answer or "chunk_id" in answer or item["citation"].get("cited_chunk_ids")
        )
        refusal_ok = _expected_refusal(row) == _actual_refusal(item["result"]) or not _expected_refusal(row)
        faithful = len(item["unsupported"]) == 0 or item["result"]["safety_result"].get("safety_label") == "refuse"
        lines.append(
            f"| {row['id']} | {has_citations} | {item['citation']['valid']} | {faithful} | {refusal_ok} | {_has_classification(answer)} |"
        )
    DAY3_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {DAY3_PATH}")


def write_day4(results: list[dict]) -> None:
    total = len(results)
    refusal_correct = sum(1 for item in results if _expected_refusal(item["row"]) == _actual_refusal(item["result"]))
    citation_valid = sum(1 for item in results if item["citation"]["valid"])
    unsupported_count = sum(len(item["unsupported"]) for item in results)
    avg_retrieval = sum(item["avg_score"] for item in results) / total if total else 0.0
    precision = sum(item["precision_at_5"] for item in results) / total if total else 0.0
    lines = [
        "# Day 4 Safety, Guardrails & Internal Evaluation",
        "",
        f"- Retrieval Precision@5 heuristic: {precision:.3f}",
        f"- Citation accuracy: {citation_valid}/{total} ({citation_valid / total:.1%})" if total else "- Citation accuracy: n/a",
        f"- Refusal accuracy: {refusal_correct}/{total} ({refusal_correct / total:.1%})" if total else "- Refusal accuracy: n/a",
        f"- Faithfulness heuristic unsupported claim count: {unsupported_count}",
        f"- Average retrieval score: {avg_retrieval:.3f}",
        "",
        "| ID | Category | Expected | Actual safety | Confidence | Unsupported claims | Avg score |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for item in results:
        row = item["row"]
        result = item["result"]
        lines.append(
            f"| {row['id']} | {row.get('category', '')} | {row['expected_behavior']} | "
            f"{result['safety_result'].get('safety_label')} | {result['confidence'].get('status')} | "
            f"{len(item['unsupported'])} | {item['avg_score']:.3f} |"
        )
    DAY4_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {DAY4_PATH}")


if __name__ == "__main__":
    run_evaluation()
