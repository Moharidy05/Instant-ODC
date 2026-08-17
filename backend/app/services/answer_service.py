from __future__ import annotations

from src.answering.answer import full_pipeline


def run_full_pipeline(question: str, disease_layer: str = "diabetes", top_k: int = 5) -> dict:
    """Thin backend wrapper around the existing src RAG pipeline."""
    return full_pipeline(query=question, disease_layer=disease_layer, top_k=top_k)
