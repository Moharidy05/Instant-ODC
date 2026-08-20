from __future__ import annotations

from typing import Any

from src.layers.disease_layer_orchestrator import resolve_disease_layer
from src.retrieval.retrieve import retrieve_chunks


def retrieve_evidence(
    query: str,
    disease_layer: str = "auto",
    top_k: int = 5,
    clinical_topic: str | None = None,
) -> dict[str, Any]:
    route = resolve_disease_layer(
        query=query,
        requested_layer=disease_layer or "auto",
    )

    if not route["can_answer"]:
        return {
            "query": query,
            "layer": route,
            "chunks": [],
        }

    effective_topic = clinical_topic or route["clinical_topic"]
    effective_layer = route["effective_layer"]
    allowed_document_ids = route["allowed_document_ids"]

    chunks = retrieve_chunks(
        query=query,
        clinical_topic=effective_topic,
        disease_layer=effective_layer,
        top_k=top_k,
        allowed_document_ids=allowed_document_ids,
    )

    return {
        "query": query,
        "layer": route,
        "chunks": chunks,
    }

