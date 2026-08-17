from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from backend.app.services.evaluation_service import run_evaluation


router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
def run(payload: EvaluationRunRequest | None = None) -> EvaluationRunResponse:
    request = payload or EvaluationRunRequest()
    return EvaluationRunResponse(**run_evaluation(limit=request.limit, disease_layer=request.disease_layer))
