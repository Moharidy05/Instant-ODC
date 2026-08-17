from __future__ import annotations

from src.answering.citation_validator import validate_citations
from src.evaluate import _actual_refusal, _expected_refusal, load_test_queries
from src.retrieval.scoring import average_similarity, precision_at_k
from src.safety.unsupported_claims import find_unsupported_claims

from backend.app.services.orchestrator_service import ask


def run_evaluation(limit: int | None = None, disease_layer: str = "diabetes") -> dict:
    rows = load_test_queries()
    if limit:
        rows = rows[:limit]
    results: list[dict] = []
    precision_total = 0.0
    citation_correct = 0
    refusal_correct = 0
    unsupported_count = 0
    score_total = 0.0

    for row in rows:
        response = ask(
            question=row["query"],
            disease_layer=disease_layer,
            language="en",
            top_k=5,
            show_chunks=True,
        )
        chunks = [chunk.model_dump() for chunk in response.retrieval.chunks]
        answer_text = response.answer if isinstance(response.answer, str) else str(response.answer)
        result_like = {"safety_result": response.safety, "answer": answer_text}
        citation = validate_citations(answer_text, chunks) if chunks else {"valid": _actual_refusal(result_like)}
        unsupported = find_unsupported_claims(answer_text, chunks) if chunks else []
        precision = precision_at_k(chunks, row.get("expected_evidence_topic", row["query"]), 5)
        avg_score = average_similarity(chunks)

        precision_total += precision
        citation_correct += 1 if citation["valid"] else 0
        refusal_correct += 1 if _expected_refusal(row) == _actual_refusal(result_like) else 0
        unsupported_count += len(unsupported)
        score_total += avg_score
        results.append(
            {
                "id": row["id"],
                "category": row.get("category"),
                "query": row["query"],
                "expected_behavior": row["expected_behavior"],
                "actual_safety": response.safety.get("safety_label"),
                "confidence": response.retrieval.confidence,
                "precision_at_5": round(precision, 3),
                "average_retrieval_score": round(avg_score, 3),
                "unsupported_claim_count": len(unsupported),
            }
        )

    total = len(rows) or 1
    return {
        "metrics": {
            "total_queries": len(rows),
            "retrieval_precision_at_5": round(precision_total / total, 3),
            "citation_accuracy": round(citation_correct / total, 3),
            "refusal_accuracy": round(refusal_correct / total, 3),
            "unsupported_claim_count": unsupported_count,
            "average_retrieval_score": round(score_total / total, 3),
        },
        "results": results,
    }
