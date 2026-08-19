from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    disease_layer: str = "diabetes"
    clinical_topic: str = "diabetes_food_safety"
    top_k: int = Field(default=10, ge=1, le=25)


class EvidenceChunk(BaseModel):
    chunk_id: str
    document_title: str | None = None
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    citation_label: str | None = None
    chunk_type: str | None = None
    disease_layer: str | None = None
    similarity: float = 0.0
    content: str


class EvidenceSearchResponse(BaseModel):
    query: str
    disease_layer: str
    chunks: list[EvidenceChunk]
