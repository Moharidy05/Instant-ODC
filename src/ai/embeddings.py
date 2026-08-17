from __future__ import annotations

from src.ai.fallback_router import get_router


def embed_text(text: str, kind: str = "document") -> list[float]:
    return get_router().embed_text(text, kind=kind)


def embed_batch(texts: list[str], kind: str = "document", batch_size: int = 20) -> list[list[float]]:
    del batch_size
    return get_router().embed_batch(texts, kind=kind)
