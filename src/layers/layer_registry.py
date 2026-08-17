from __future__ import annotations

from src.core.config import project_path, parse_simple_yaml


ALIASES = {
    "diabetes": "diabetes",
    "diabetes + kidney disease": "diabetes_ckd",
    "diabetes_ckd": "diabetes_ckd",
    "ckd": "diabetes_ckd",
    "diabetes + cardiovascular disease": "diabetes_cvd",
    "diabetes_cvd": "diabetes_cvd",
    "cvd": "diabetes_cvd",
    "heart": "diabetes_cvd",
    "diabetes + pregnancy": "diabetes_pregnancy",
    "diabetes_pregnancy": "diabetes_pregnancy",
    "pregnancy": "diabetes_pregnancy",
    "diabetes + hypertension": "diabetes_hypertension",
    "diabetes_hypertension": "diabetes_hypertension",
    "hypertension": "diabetes_hypertension",
}


def normalize_layer(layer: str) -> str:
    return ALIASES.get((layer or "diabetes").strip().lower(), "diabetes")


def load_layer_registry() -> dict:
    path = project_path("config", "disease_layers.yaml")
    if not path.exists():
        return {"layers": {"diabetes": {"active": True, "clinical_topic": "diabetes_food_safety", "required_documents": []}}}
    return parse_simple_yaml(path)


def get_layer(layer: str) -> dict:
    registry = load_layer_registry().get("layers", {})
    normalized = normalize_layer(layer)
    return registry.get(normalized, registry.get("diabetes", {}))
