from __future__ import annotations

from src.food.substitutions import suggest_substitutions
from src.retrieval.retrieve import retrieve_chunks


def get_substitutions(food: str, disease_layer: str = "diabetes", language: str = "en") -> list[dict]:
    del language
    query = f"What can a person with diabetes eat or drink instead of {food}?"
    chunks = retrieve_chunks(query, disease_layer=disease_layer, top_k=8)
    return suggest_substitutions(food, chunks)
