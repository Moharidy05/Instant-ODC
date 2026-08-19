from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.evidence import EvidenceChunk, EvidenceSearchRequest, EvidenceSearchResponse
from backend.app.services.retrieval_service import retrieve_evidence


router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/search", response_model=EvidenceSearchResponse)
def search_evidence(payload: EvidenceSearchRequest) -> EvidenceSearchResponse:
    result = retrieve_evidence(
        payload.query,
        disease_layer=payload.disease_layer,
        clinical_topic=payload.clinical_topic,
        top_k=payload.top_k,
    )
    return EvidenceSearchResponse(
        query=payload.query,
        disease_layer=payload.disease_layer,
        chunks=[EvidenceChunk(**chunk) for chunk in result["chunks"]],
    )
