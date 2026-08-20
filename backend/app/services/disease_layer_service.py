from __future__ import annotations

from src.layers.disease_layer_orchestrator import layer_status_rows, resolve_disease_layer


def get_layers() -> list[dict]:
    return layer_status_rows()


def resolve_layer(question: str, selected_layer: str = "auto") -> dict:
    return resolve_disease_layer(question, selected_layer)

