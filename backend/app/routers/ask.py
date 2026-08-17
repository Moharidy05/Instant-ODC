from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.ask import AskRequest, AskResponse
from backend.app.services.orchestrator_service import ask


router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    return ask(
        question=payload.question,
        disease_layer=payload.disease_layer,
        language=payload.language,
        top_k=payload.top_k,
        show_chunks=payload.show_chunks,
    )
