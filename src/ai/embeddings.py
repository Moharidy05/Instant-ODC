from __future__ import annotations

from src.core.config import EMBEDDING_PROVIDER


def embed_text(text: str, kind: str = "document") -> list[float]:
    """Embed a single text using the configured provider."""
    if EMBEDDING_PROVIDER == "embeddinggemma_api":
        from src.ai.embedding_api import embed_query
        return embed_query(text)
    if EMBEDDING_PROVIDER == "gemini":
        from src.ai.fallback_router import get_router
        return get_router().embed_text(text, kind=kind)
    if EMBEDDING_PROVIDER == "local":
        from src.ai.local_embeddings import embed_text_local
        return embed_text_local(text, kind=kind)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r}")

def embed_batch(
    texts: list[str],
    kind: str = "document",
    batch_size: int = 10,
) -> list[list[float]]:
    """Embed a batch of texts using the configured provider."""
    if EMBEDDING_PROVIDER == "embeddinggemma_api":
        from src.ai.embedding_api import embed_query
        return [embed_query(text) for text in texts]

    if EMBEDDING_PROVIDER == "gemini":
        from src.ai.fallback_router import get_router
        return get_router().embed_batch(texts, kind=kind)

    if EMBEDDING_PROVIDER == "local":
        from src.ai.local_embeddings import embed_batch_local
        return embed_batch_local(texts, kind=kind, batch_size=batch_size)

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r}")