"""
Google Gemini embeddings wrapper for the RAG pipeline.
Uses Gemini embedding model to generate vectors for chunks and queries.
"""

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, EMBEDDING_DIM

_client = genai.Client(api_key=GEMINI_API_KEY)


def embed_text(text: str, kind: str = "document") -> list[float]:
    """
    Generate a single embedding vector.
    Recommended model for this MVP:
    gemini-embedding-001
    """

    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot embed empty text.")

    task_type = "RETRIEVAL_DOCUMENT" if kind == "document" else "RETRIEVAL_QUERY"

    response = _client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIM,
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embeddings.")

    values = list(response.embeddings[0].values)

    if len(values) != EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding dimension mismatch. Expected {EMBEDDING_DIM}, got {len(values)}."
        )

    return values


def embed_batch(
    texts: list[str],
    kind: str = "document",
    batch_size: int = 20,
) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Important:
    This implementation embeds one text at a time to avoid Gemini Embedding 2
    aggregation behavior and to guarantee one vector per chunk.
    """

    all_embeddings = []

    for idx, text in enumerate(texts, start=1):
        try:
            emb = embed_text(text, kind=kind)
            all_embeddings.append(emb)
        except Exception as e:
            raise RuntimeError(f"Failed to embed item {idx}/{len(texts)}: {e}")

    if len(all_embeddings) != len(texts):
        raise RuntimeError(
            f"Embedding count mismatch. Expected {len(texts)}, got {len(all_embeddings)}."
        )

    return all_embeddings