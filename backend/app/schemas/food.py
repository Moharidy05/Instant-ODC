from __future__ import annotations

from pydantic import BaseModel, Field


class FoodGuidanceItem(BaseModel):
    food: str
    note: str = ""
    evidence_chunk_id: str
    citation_label: str


class FoodGuidanceListResponse(BaseModel):
    disease_layer: str
    encouraged: list[FoodGuidanceItem]
    suitable_with_caution: list[FoodGuidanceItem]
    better_to_limit: list[FoodGuidanceItem]


class SubstitutionRequest(BaseModel):
    food: str = Field(min_length=1)
    disease_layer: str = "diabetes"
    language: str = "en"


class SubstitutionItem(BaseModel):
    instead_of: str
    alternative: str
    evidence_chunk_id: str
    citation_label: str


class SubstitutionResponse(BaseModel):
    food: str
    disease_layer: str
    alternatives: list[SubstitutionItem]
