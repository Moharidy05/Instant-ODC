from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.layers import LayersResponse
from backend.app.services.disease_layer_service import get_layers


router = APIRouter(tags=["layers"])


@router.get("/layers", response_model=LayersResponse)
def layers() -> LayersResponse:
    return LayersResponse(layers=get_layers())
