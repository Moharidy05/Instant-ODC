from __future__ import annotations

import re
from typing import Any

from src.layers.layer_registry import (
    LAYER_REGISTRY,
    get_layer_config,
)


SPECIFIC_LAYER_PATTERNS: dict[str, list[str]] = {
    "diabetes_ckd": [
        r"\bckd\b",
        r"chronic kidney disease",
        r"kidney disease",
        r"renal disease",
        r"renal impairment",
        r"\bdialysis\b",
        r"\begfr\b",
        r"albuminuria",
        r"kidney failure",
        r"phosphorus",
        r"phosphate",
        r"potassium",
    ],

    "diabetes_cvd": [
        r"cardiovascular",
        r"heart disease",
        r"coronary",
        r"\bcvd\b",
        r"atheroscler",
        r"heart attack",
        r"myocardial",
        r"stroke",
        r"heart failure",
        r"hypertension",
        r"high blood pressure",
    ],

    "diabetes_foot": [
        r"diabetic foot",
        r"foot ulcer",
        r"foot wound",
        r"foot infection",
        r"neuropathic ulcer",
        r"offloading",
        r"amputation",
        r"foot disease",
    ],

    "diabetes_masld": [
        r"\bmasld\b",
        r"\bnafld\b",
        r"fatty liver",
        r"metabolic dysfunction.*liver",
        r"steatotic liver",
        r"hepatic steatosis",
    ],
}


GENERAL_DIABETES_PATTERNS = [
    r"\bdiabetes\b",
    r"\bdiabetic\b",
    r"blood sugar",
    r"blood glucose",
    r"\bglucose\b",
    r"\ba1c\b",
    r"prediabetes",
]


FOOD_PATTERNS = [
    r"\bfood\b",
    r"\beat\b",
    r"\beating\b",
    r"\bdrink\b",
    r"\bbeverage\b",
    r"\bdiet\b",
    r"\bnutrition\b",
    r"\bmeal\b",
    r"\bfruit\b",
    r"\bjuice\b",
    r"\bsoda\b",
    r"\bwater\b",
    r"\bcarb",
    r"carbohydrate",
    r"\bprotein\b",
    r"\bfat\b",
    r"\bfiber\b",
    r"\bsodium\b",
    r"\bsalt\b",
    r"\brice\b",
    r"\bbread\b",
    r"\bpasta\b",
    r"\bbanana\b",
    r"\bapple\b",
    r"\borange\b",
    r"vegetable",
    r"legume",
    r"\bbeans?\b",
    r"lentil",
    r"\bnuts?\b",
    r"whole grain",
    r"processed food",
    r"sweetener",
]


def _matches(patterns: list[str], query: str) -> bool:
    return any(
        re.search(pattern, query, flags=re.IGNORECASE)
        for pattern in patterns
    )


def route_question(
    query: str,
    requested_layer: str | None = "auto",
) -> dict[str, Any]:
    query = (query or "").strip()

    if not query:
        return {
            "effective_layer": None,
            "clinical_topic": None,
            "allowed_document_ids": [],
            "can_answer": False,
            "route_status": "invalid",
            "reason": "Empty query.",
        }

    # Explicit developer/debug override.
    # Public frontend should send "auto".
    if requested_layer and requested_layer not in {"auto", ""}:
        cfg = get_layer_config(requested_layer)

        if not cfg:
            return {
                "effective_layer": None,
                "clinical_topic": None,
                "allowed_document_ids": [],
                "can_answer": False,
                "route_status": "invalid_layer",
                "reason": f"Unknown disease layer: {requested_layer}",
            }

        if not cfg.get("active"):
            return {
                "effective_layer": requested_layer,
                "clinical_topic": cfg.get("clinical_topic"),
                "allowed_document_ids": cfg.get("document_ids", []),
                "can_answer": False,
                "route_status": "inactive_layer",
                "reason": f"Disease layer {requested_layer} is inactive.",
            }

        return {
            "effective_layer": requested_layer,
            "clinical_topic": cfg["clinical_topic"],
            "allowed_document_ids": list(cfg["document_ids"]),
            "can_answer": True,
            "route_status": "explicit_override",
            "reason": f"Explicit layer override: {requested_layer}.",
        }

    matched_specific_layers: list[str] = []

    for layer, patterns in SPECIFIC_LAYER_PATTERNS.items():
        if _matches(patterns, query):
            matched_specific_layers.append(layer)

    # For now, one-primary-layer policy.
    if len(matched_specific_layers) > 1:
        return {
            "effective_layer": None,
            "clinical_topic": None,
            "allowed_document_ids": [],
            "can_answer": False,
            "route_status": "ambiguous_multi_layer",
            "matched_layers": matched_specific_layers,
            "reason": (
                "The question matches more than one specific disease layer. "
                "This version intentionally uses one primary guideline layer at a time."
            ),
        }

    if len(matched_specific_layers) == 1:
        layer = matched_specific_layers[0]
        cfg = LAYER_REGISTRY[layer]

        return {
            "effective_layer": layer,
            "clinical_topic": cfg["clinical_topic"],
            "allowed_document_ids": list(cfg["document_ids"]),
            "can_answer": bool(cfg["active"]),
            "route_status": "specific_layer",
            "reason": f"Question matched the {layer} disease layer.",
        }

    # A general food/nutrition question inside this application
    # defaults to the general diabetes nutrition guideline.
    if _matches(GENERAL_DIABETES_PATTERNS, query) or _matches(FOOD_PATTERNS, query):
        cfg = LAYER_REGISTRY["diabetes"]

        return {
            "effective_layer": "diabetes",
            "clinical_topic": cfg["clinical_topic"],
            "allowed_document_ids": list(cfg["document_ids"]),
            "can_answer": True,
            "route_status": "general_diabetes",
            "reason": (
                "General diabetes food/nutrition question routed to ADA nutrition evidence."
            ),
        }

    return {
        "effective_layer": None,
        "clinical_topic": None,
        "allowed_document_ids": [],
        "can_answer": False,
        "route_status": "out_of_scope",
        "reason": "Question is outside the indexed diabetes guideline scope.",
    }
