from __future__ import annotations

from pydantic import BaseModel


class DiseaseLayerStatus(BaseModel):
    layer: str
    active: bool
    required_documents: list[str]
    description: str = ""


class LayersResponse(BaseModel):
    layers: list[DiseaseLayerStatus]
