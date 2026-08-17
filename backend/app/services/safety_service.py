from __future__ import annotations

from src.safety.safety import classify_query


def classify_safety(question: str, active_layer: str = "diabetes") -> dict:
    return classify_query(question, active_layer=active_layer)
