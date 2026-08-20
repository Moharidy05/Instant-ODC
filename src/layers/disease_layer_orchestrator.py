from __future__ import annotations

from typing import Any

from src.layers.disease_layer_router import route_question
from src.layers.layer_registry import (
    LAYER_REGISTRY,
    get_layer_config,
    layer_status_rows,
)


def resolve_disease_layer(
    query: str,
    requested_layer: str | None = "auto",
) -> dict[str, Any]:
    return route_question(
        query=query,
        requested_layer=requested_layer,
    )


def is_layer_active(layer: str) -> bool:
    cfg = get_layer_config(layer)
    return bool(cfg and cfg.get("active"))


def get_layer_documents(layer: str) -> list[str]:
    cfg = get_layer_config(layer)
    if not cfg:
        return []
    return list(cfg.get("document_ids") or [])


# Backward compatibility alias
orchestrate_disease_layer = resolve_disease_layer


__all__ = [
    "LAYER_REGISTRY",
    "resolve_disease_layer",
    "orchestrate_disease_layer",
    "layer_status_rows",
    "is_layer_active",
    "get_layer_documents",
]

