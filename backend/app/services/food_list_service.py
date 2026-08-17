from __future__ import annotations

from src.food.food_lists import build_food_guidance_lists
from src.retrieval.retrieve import retrieve_chunks


def get_guidance_list(disease_layer: str = "diabetes") -> dict:
    chunks = retrieve_chunks(
        "diabetes nutrition foods encouraged caution better to limit whole grains legumes beverages sodium processed foods",
        disease_layer=disease_layer,
        top_k=25,
    )
    return build_food_guidance_lists(chunks)
