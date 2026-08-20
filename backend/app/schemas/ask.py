from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.evidence import EvidenceChunk
from backend.app.schemas.food import SubstitutionItem


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    disease_layer: str = "auto"
    language: str = "en"
    top_k: int = Field(default=5, ge=1, le=10)
    show_chunks: bool = False


class RetrievalPayload(BaseModel):
    confidence: str
    top_score: float
    chunks: list[EvidenceChunk]


class CitationPayload(BaseModel):
    document_name: str
    section_title: str
    page_number: int | None = None
    chunk_id: str
    citation_label: str = ""


class AnswerPayload(BaseModel):
    classification: str
    short_answer: str
    why: str
    better_alternatives: list[SubstitutionItem | str]
    citations: list[CitationPayload]
    safety_note: str


class UnsupportedClaim(BaseModel):
    sentence: str
    overlap: float


class AskResponse(BaseModel):
    question: str
    layer: dict[str, Any]
    safety: dict[str, Any]
    confidence: dict[str, Any]
    retrieval: RetrievalPayload
    answer: str | AnswerPayload | dict[str, Any]
    substitutions: list[SubstitutionItem | dict[str, Any]]
    citation_validation: dict[str, Any]
    unsupported_claims: list[UnsupportedClaim]
