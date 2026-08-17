from __future__ import annotations

from src.core.config import MIN_RETRIEVAL_CONFIDENCE


def retrieval_confidence(chunks: list[dict], threshold: float = MIN_RETRIEVAL_CONFIDENCE) -> dict:
    top = max((float(c.get("similarity", 0.0) or 0.0) for c in chunks), default=0.0)
    return {
        "top_similarity": top,
        "threshold": threshold,
        "status": "sufficient" if top >= threshold else "insufficient",
        "can_answer": top >= threshold,
    }
