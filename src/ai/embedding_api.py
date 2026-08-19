from __future__ import annotations

from typing import Any

import httpx

from src.core.config import (
    EMBEDDING_API_KEY,
    EMBEDDING_API_MODEL,
    EMBEDDING_API_STYLE,
    EMBEDDING_API_TIMEOUT_SECONDS,
    EMBEDDING_API_URL,
    EMBEDDING_DIM,
    EMBEDDING_PROVIDER,
)


def _build_payload(text: str) -> dict:
    """
    Supports Ollama-style /api/embed:
    {
        "model": "embeddinggemma",
        "input": "text"
    }

    Also supports simple custom style:
    {
        "text": "text"
    }
    """
    if EMBEDDING_API_STYLE == "ollama":
        return {
            "model": EMBEDDING_API_MODEL,
            "input": text,
        }

    if EMBEDDING_API_STYLE == "simple":
        return {
            "text": text,
        }

    raise RuntimeError(
        f"Unsupported EMBEDDING_API_STYLE={EMBEDDING_API_STYLE}. "
        "Expected ollama or simple."
    )


def _extract_vector(response_json: Any) -> list[float]:
    """
    Supports common response shapes:
    Ollama /api/embed:
      {"embeddings": [[...]]}

    Other possible formats:
      {"embedding": [...]}
      {"vector": [...]}
      {"data": [{"embedding": [...]}]}
      [...]
    """
    if isinstance(response_json, list):
        if response_json and isinstance(response_json[0], (int, float)):
            return [float(x) for x in response_json]

        if response_json and isinstance(response_json[0], list):
            return [float(x) for x in response_json[0]]

    if isinstance(response_json, dict):
        if isinstance(response_json.get("embedding"), list):
            return [float(x) for x in response_json["embedding"]]

        if isinstance(response_json.get("vector"), list):
            return [float(x) for x in response_json["vector"]]

        embeddings = response_json.get("embeddings")
        if isinstance(embeddings, list) and embeddings:
            if isinstance(embeddings[0], list):
                return [float(x) for x in embeddings[0]]
            if isinstance(embeddings[0], (int, float)):
                return [float(x) for x in embeddings]

        data = response_json.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and isinstance(first.get("embedding"), list):
                return [float(x) for x in first["embedding"]]

    raise ValueError(
        f"Embedding API response does not contain a valid embedding. "
        f"Response keys: {list(response_json.keys()) if isinstance(response_json, dict) else type(response_json)}"
    )


def embed_query(text: str) -> list[float]:
    if EMBEDDING_PROVIDER != "embeddinggemma_api":
        raise RuntimeError(
            f"Unsupported EMBEDDING_PROVIDER={EMBEDDING_PROVIDER}. "
            "Expected embeddinggemma_api."
        )

    if EMBEDDING_DIM != 768:
        raise RuntimeError(f"EMBEDDING_DIM must be 768, got {EMBEDDING_DIM}.")

    if not EMBEDDING_API_URL:
        raise RuntimeError("EMBEDDING_API_URL is missing.")

    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot embed an empty query.")

    headers = {
        "Content-Type": "application/json",
    }

    if EMBEDDING_API_KEY:
        headers["Authorization"] = f"Bearer {EMBEDDING_API_KEY}"

    payload = _build_payload(text)

    try:
        with httpx.Client(timeout=EMBEDDING_API_TIMEOUT_SECONDS) as client:
            response = client.post(
                EMBEDDING_API_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            response_json = response.json()
    except Exception as exc:
        raise RuntimeError(
            f"Embedding API request failed. "
            f"URL={EMBEDDING_API_URL}, style={EMBEDDING_API_STYLE}, model={EMBEDDING_API_MODEL}. "
            f"Original error: {exc}"
        ) from exc

    vector = _extract_vector(response_json)

    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch. Expected {EMBEDDING_DIM}, got {len(vector)}."
        )

    return vector
