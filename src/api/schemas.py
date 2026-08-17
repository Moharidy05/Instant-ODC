from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    disease_layer: str = "diabetes"
    top_k: int = 5


class RetrievedChunk(BaseModel):
    chunk_id: str
    section_title: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    similarity: float | None = None
    citation_label: str | None = None
    content: str


class AskResponse(BaseModel):
    query: str
    safety_result: dict
    confidence: dict
    chunks: list[RetrievedChunk]
    answer: str
