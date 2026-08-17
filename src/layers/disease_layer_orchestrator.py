from __future__ import annotations

import re

from src.layers.layer_registry import get_layer, load_layer_registry, normalize_layer


QUERY_LAYER_HINTS = [
    (r"(kidney|renal|ckd)", "diabetes_ckd"),
    (r"(heart|cardiovascular|cvd)", "diabetes_cvd"),
    (r"(pregnan|gestational)", "diabetes_pregnancy"),
    (r"(hypertension|blood pressure)", "diabetes_hypertension"),
]


def infer_required_layer(query: str, selected_layer: str) -> str:
    selected = normalize_layer(selected_layer)
    q = (query or "").lower()
    for pattern, layer in QUERY_LAYER_HINTS:
        if re.search(pattern, q):
            return layer
    return selected


def orchestrate_disease_layer(
    user_query: str,
    selected_disease_layer: str = "diabetes",
    active_indexed_documents: list[str] | None = None,
) -> dict:
    available = active_indexed_documents or ["ada_standards_2026_section_5"]
    effective_layer = infer_required_layer(user_query, selected_disease_layer)
    layer = get_layer(effective_layer)
    required = layer.get("required_documents", []) or []
    active = bool(layer.get("active", False))
    docs_available = all(doc in available for doc in required)
    can_answer = active and docs_available

    reason = "Layer is active and required evidence documents are indexed."
    if effective_layer != normalize_layer(selected_disease_layer):
        reason = "Query mentions a comorbidity requiring a specific inactive guideline layer."
    if not active:
        reason = f"Disease layer '{effective_layer}' is inactive until its official guideline is indexed."
    elif not docs_available:
        reason = f"Disease layer '{effective_layer}' is missing required indexed documents."

    return {
        "effective_layer": effective_layer,
        "active": active,
        "required_documents": required,
        "available_documents": available,
        "can_answer": can_answer,
        "reason": reason,
        "retrieval_filters": {
            "clinical_topic": layer.get("clinical_topic", "diabetes_food_safety"),
            "disease_layer": effective_layer if effective_layer != "diabetes" else "diabetes",
        },
    }


def layer_status_rows() -> list[dict]:
    registry = load_layer_registry().get("layers", {})
    return [
        {
            "layer": name,
            "active": bool(meta.get("active")),
            "required_documents": meta.get("required_documents", []),
            "description": meta.get("description", ""),
        }
        for name, meta in registry.items()
    ]
