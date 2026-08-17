from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.schemas.food import FoodGuidanceListResponse, SubstitutionRequest, SubstitutionResponse
from backend.app.services.food_list_service import get_guidance_list
from backend.app.services.substitution_service import get_substitutions


router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/guidance-list", response_model=FoodGuidanceListResponse)
def guidance_list(disease_layer: str = Query(default="diabetes")) -> FoodGuidanceListResponse:
    lists = get_guidance_list(disease_layer)
    return FoodGuidanceListResponse(disease_layer=disease_layer, **lists)


@router.post("/substitutions", response_model=SubstitutionResponse)
def substitutions(payload: SubstitutionRequest) -> SubstitutionResponse:
    return SubstitutionResponse(
        food=payload.food,
        disease_layer=payload.disease_layer,
        alternatives=get_substitutions(payload.food, payload.disease_layer, payload.language),
    )
