from __future__ import annotations

import logging
from typing import Optional

from src.core.config import EMBEDDING_DIM, LOCAL_EMBEDDING_FALLBACK_MODEL, LOCAL_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_model: Optional[object] = None
_model_name: Optional[str] = None


def get_local_embedding_model() -> tuple[object, str]:
    """Load and cache a SentenceTransformer model.

    Tries LOCAL_EMBEDDING_MODEL first, falls back to LOCAL_EMBEDDING_FALLBACK_MODEL.
    """
    global _model, _model_name
    if _model is not None:
        return _model, _model_name  # type: ignore[return-value]

    from sentence_transformers import SentenceTransformer

    for name in (LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_FALLBACK_MODEL):
        try:
            logger.info("Loading local embedding model: %s", name)
            _model = SentenceTransformer(name)
            _model_name = name
            logger.info("Loaded local embedding model: %s", name)
            return _model, _model_name
        except Exception as exc:
            logger.warning("Failed to load model %s: %s", name, exc)
            continue

    raise RuntimeError(
        f"Could not load any local embedding model. "
        f"Tried: {LOCAL_EMBEDDING_MODEL}, {LOCAL_EMBEDDING_FALLBACK_MODEL}"
    )


def _is_bge_model(name: str) -> bool:
    """Check if the model is a BGE model that needs query prefixing."""
    return "bge" in name.lower()


def _prepare_text(text: str, kind: str, model_name: str) -> str:
    """Add instruction prefix for BGE models."""
    if not _is_bge_model(model_name):
        return text
    if kind == "query":
        return f"Represent this sentence for searching relevant passages: {text}"
    return text


def embed_text_local(text: str, kind: str = "document") -> list[float]:
    """Embed a single text using the local SentenceTransformer model."""
    model, model_name = get_local_embedding_model()
    prepared = _prepare_text(text.strip(), kind, model_name)
    vector = model.encode(prepared, normalize_embeddings=True)  # type: ignore[union-attr]
    result = vector.tolist()
    if len(result) != EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding dimension mismatch. Expected {EMBEDDING_DIM}, got {len(result)}."
        )
    return result


def embed_batch_local(
    texts: list[str],
    kind: str = "document",
    batch_size: int = 32,
) -> list[list[float]]:
    """Embed a batch of texts using the local SentenceTransformer model."""
    if not texts:
        raise ValueError("Cannot embed empty text list.")

    model, model_name = get_local_embedding_model()
    prepared = [_prepare_text(t.strip(), kind, model_name) for t in texts]
    vectors = model.encode(prepared, normalize_embeddings=True, batch_size=batch_size)  # type: ignore[union-attr]

    results: list[list[float]] = []
    for idx, vec in enumerate(vectors):
        row = vec.tolist()
        if len(row) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Embedding dimension mismatch for item {idx + 1}. "
                f"Expected {EMBEDDING_DIM}, got {len(row)}."
            )
        results.append(row)
    return results
