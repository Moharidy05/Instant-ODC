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
        layer=result.get("layer"),
        disease_layer=result.get("layer", {}).get("effective_layer") or payload.disease_layer,
        chunks=[
            EvidenceChunk(
                chunk_id=str(chunk.get("chunk_id", "")),
                document_id=chunk.get("document_id"),
                document_title=chunk.get("document_title"),
                section_title=chunk.get("section_title"),
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                citation_label=chunk.get("citation_label"),
                chunk_type=chunk.get("chunk_type"),
                disease_layer=chunk.get("disease_layer"),
                similarity=float(chunk.get("similarity", 0.0) or 0.0),
                content=chunk.get("content", ""),
            )
            for chunk in result.get("chunks", [])
        ],
    )
