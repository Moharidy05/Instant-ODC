from __future__ import annotations

from typing import Any


LAYER_REGISTRY: dict[str, dict[str, Any]] = {
    "diabetes": {
        "label": "General Diabetes / Nutrition",
        "active": True,
        "clinical_topic": "diabetes_food_safety",
        "document_ids": [
            "ada_standards_2026_section_5",
        ],
        "description": (
            "General diabetes food, beverage and nutrition questions."
        ),
    },

    "diabetes_ckd": {
        "label": "Diabetes + CKD",
        "active": True,
        "clinical_topic": "diabetes_ckd",
        "document_ids": [
            "kdigo_2022_diabetes_ckd",
        ],
        "description": (
            "Questions specifically involving diabetes with chronic kidney disease."
        ),
    },

    "diabetes_cvd": {
        "label": "Diabetes + Cardiovascular Disease",
        "active": True,
        "clinical_topic": "diabetes_cvd",
        "document_ids": [
            "ada_2024_section_10_cvd",
        ],
        "description": (
            "Questions specifically involving diabetes with cardiovascular disease."
        ),
    },

    "diabetes_foot": {
        "label": "Diabetes-related Foot Disease",
        "active": True,
        "clinical_topic": "diabetes_foot",
        "document_ids": [
            "iwgdf_2023_practical_diabetes_foot",
            "iwgdf_2023_prevention_diabetes_foot",
            "iwgdf_2023_classification_diabetes_foot",
        ],
        "description": (
            "Questions specifically involving diabetes-related foot disease."
        ),
    },

    "diabetes_masld": {
        "label": "Diabetes + MASLD",
        "active": True,
        "clinical_topic": "diabetes_masld",
        "document_ids": [
            "masld_metabolic_disease_guideline",
        ],
        "description": (
            "Questions specifically involving diabetes with fatty liver / MASLD."
        ),
    },

    "inactive_misc": {
        "label": "Inactive Miscellaneous Evidence",
        "active": False,
        "clinical_topic": "diabetes_misc",
        "document_ids": [
            "additional_diabetes_guideline_dci260082",
        ],
        "description": (
            "Inactive miscellaneous evidence. Never use automatically."
        ),
    },
}


def get_layer_config(layer: str) -> dict[str, Any] | None:
    return LAYER_REGISTRY.get(layer)


def get_active_layers() -> list[str]:
    return [
        name
        for name, cfg in LAYER_REGISTRY.items()
        if cfg.get("active")
    ]


def layer_status_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for name, cfg in LAYER_REGISTRY.items():
        rows.append(
            {
                "layer": name,
                "label": cfg.get("label"),
                "active": bool(cfg.get("active")),
                "clinical_topic": cfg.get("clinical_topic"),
                "required_documents": list(cfg.get("document_ids") or []),
                "available_documents": list(cfg.get("document_ids") or []),
                "description": cfg.get("description"),
            }
        )

    return rows

