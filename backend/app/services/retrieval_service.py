from __future__ import annotations

from src.core.config import PROJECT_TOPIC
from src.retrieval.retrieve import retrieve_chunks
from src.safety.confidence import retrieval_confidence


def retrieve_evidence(
    query: str,
    disease_layer: str = "diabetes",
    top_k: int = 5,
    clinical_topic: str = PROJECT_TOPIC,
) -> dict:
    chunks = retrieve_chunks(query, clinical_topic=clinical_topic, disease_layer=disease_layer, top_k=top_k)
    confidence = retrieval_confidence(chunks)
    return {
        "confidence": confidence["status"],
        "top_score": float(confidence["top_similarity"]),
        "chunks": chunks,
    }
