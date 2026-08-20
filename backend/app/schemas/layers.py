from __future__ import annotations

from pydantic import BaseModel, Field


class DiseaseLayerStatus(BaseModel):
    layer: str
    label: str | None = None
    active: bool
    clinical_topic: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    available_documents: list[str] = Field(default_factory=list)
    description: str = ""


class LayersResponse(BaseModel):
    layers: list[DiseaseLayerStatus]

