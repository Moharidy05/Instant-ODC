from __future__ import annotations

from pydantic import BaseModel


class EvaluationRunRequest(BaseModel):
    limit: int | None = None
    disease_layer: str = "diabetes"


class EvaluationMetrics(BaseModel):
    total_queries: int
    retrieval_precision_at_5: float
    citation_accuracy: float
    refusal_accuracy: float
    unsupported_claim_count: int
    average_retrieval_score: float


class EvaluationRunResponse(BaseModel):
    metrics: EvaluationMetrics
    results: list[dict]
