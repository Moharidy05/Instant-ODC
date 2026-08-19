from __future__ import annotations

from src.core.config import MIN_RETRIEVAL_CONFIDENCE
from src.retrieval.scoring import keyword_overlap_score


def retrieval_confidence(
    chunks: list[dict],
    threshold: float = MIN_RETRIEVAL_CONFIDENCE,
    query: str | None = None,
) -> dict:
    top_chunk = max(chunks, key=lambda c: float(c.get("similarity", 0.0) or 0.0), default={})
    top = float(top_chunk.get("similarity", 0.0) or 0.0)
    lexical = None
    weak_relevance = False
    if query and top_chunk:
        haystack = " ".join(
            str(top_chunk.get(field, "") or "")
            for field in ("section_title", "chunk_type", "content", "citation_label")
        )
        lexical = keyword_overlap_score(query, haystack)
        weak_relevance = top >= threshold and lexical < 0.12
    status = "sufficient" if top >= threshold else "insufficient"
    can_answer = top >= threshold
    if weak_relevance:
        status = "weak_relevance"
        can_answer = False
    return {
        "top_similarity": top,
        "threshold": threshold,
        "top_lexical_overlap": lexical,
        "status": status,
        "can_answer": can_answer,
    }
