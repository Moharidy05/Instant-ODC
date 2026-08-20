from __future__ import annotations

from typing import Any

from src.core.config import MIN_RETRIEVAL_CONFIDENCE
from src.retrieval.scoring import lexical_similarity


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluate_retrieval_confidence(
    query: str,
    chunks: list[dict[str, Any]],
    expected_layer: str,
    threshold: float = MIN_RETRIEVAL_CONFIDENCE,
) -> dict[str, Any]:
    if not chunks:
        return {
            "top_similarity": 0.0,
            "top_lexical_overlap": 0.0,
            "layer_match": 0.0,
            "evidence_count": 0,
            "composite_score": 0.0,
            "threshold": threshold,
            "status": "insufficient",
            "can_answer": False,
        }

    top_similarity = max(
        _clamp(float(chunk.get("similarity") or 0.0))
        for chunk in chunks
    )

    lexical_scores: list[float] = []

    for chunk in chunks:
        evidence_text = " ".join(
            [
                str(chunk.get("section_title") or ""),
                str(chunk.get("chunk_type") or ""),
                str(chunk.get("content") or ""),
            ]
        )

        lexical_scores.append(
            _clamp(
                lexical_similarity(
                    query,
                    evidence_text,
                )
            )
        )

    top_lexical_overlap = max(lexical_scores or [0.0])

    matching_layer_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("disease_layer") == expected_layer
    ]

    layer_match = (
        1.0
        if matching_layer_chunks
        else 0.0
    )

    evidence_count = len(chunks)

    evidence_coverage = min(
        evidence_count / 3.0,
        1.0,
    )

    # Deliberately combines semantic similarity with lexical evidence,
    # routing correctness and availability of multiple evidence chunks.
    composite_score = (
        (0.60 * top_similarity)
        + (0.25 * top_lexical_overlap)
        + (0.10 * layer_match)
        + (0.05 * evidence_coverage)
    )

    composite_score = round(
        _clamp(composite_score),
        4,
    )

    sufficient = (
        composite_score >= threshold
        and layer_match > 0
        and evidence_count > 0
    )

    return {
        "top_similarity": round(top_similarity, 4),
        "top_lexical_overlap": round(top_lexical_overlap, 4),
        "layer_match": layer_match,
        "evidence_count": evidence_count,
        "composite_score": composite_score,
        "threshold": threshold,
        "status": "sufficient" if sufficient else "insufficient",
        "can_answer": sufficient,
    }
