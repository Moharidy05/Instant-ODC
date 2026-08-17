from __future__ import annotations

import json
from pathlib import Path

from src.ai.embeddings import embed_text
from src.core.config import PROJECT_TOPIC, RETRIEVAL_CANDIDATE_K, RETRIEVAL_TOP_K, project_path
from src.core.errors import RetrievalError
from src.core.logging import utc_now_iso
from src.db.supabase_client import get_admin_client, get_client, supabase_configured
from src.retrieval.rerank import rerank_chunks
from src.retrieval.scoring import lexical_similarity


def retrieve_chunks(
    query: str,
    clinical_topic: str = PROJECT_TOPIC,
    disease_layer: str = "diabetes",
    top_k: int = RETRIEVAL_TOP_K,
    candidate_k: int = RETRIEVAL_CANDIDATE_K,
    log: bool = True,
) -> list[dict]:
    """Retrieve top-k evidence chunks.

    Production path uses Supabase pgvector. If Supabase/Gemini are not configured,
    a local lexical fallback over data/chunks/chunks.jsonl is used for demos/tests.
    """
    query = (query or "").strip()
    if not query:
        return []

    if not supabase_configured(admin=False):
        return local_retrieve_chunks(query, clinical_topic, disease_layer, top_k)

    try:
        query_embedding = embed_text(query, kind="query")
        client = get_client()
        response = client.rpc(
            "match_guideline_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": max(candidate_k, top_k),
                "filter_clinical_topic": clinical_topic,
                "filter_disease_layer": disease_layer,
            },
        ).execute()
        candidates = response.data or []
        results = rerank_chunks(query, candidates, top_k)
        if log:
            log_retrieval_results(query, disease_layer, results)
        return results
    except Exception as exc:
        raise RetrievalError(f"Retrieval failed: {exc}") from exc


def local_retrieve_chunks(
    query: str,
    clinical_topic: str = PROJECT_TOPIC,
    disease_layer: str = "diabetes",
    top_k: int = RETRIEVAL_TOP_K,
    chunks_path: str | Path | None = None,
) -> list[dict]:
    path = Path(chunks_path) if chunks_path else project_path("data", "chunks", "chunks.jsonl")
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            chunk = json.loads(line)
            if chunk.get("clinical_topic") != clinical_topic:
                continue
            if chunk.get("disease_layer") != disease_layer:
                continue
            score = lexical_similarity(
                query,
                " ".join(
                    str(chunk.get(field, ""))
                    for field in ("section_title", "chunk_type", "content", "citation_label")
                ),
            )
            item = dict(chunk)
            item["similarity"] = round(score, 4)
            rows.append(item)
    return sorted(rows, key=lambda x: x.get("similarity", 0), reverse=True)[:top_k]


def log_retrieval_results(query: str, layer: str, chunks: list[dict]) -> None:
    if not supabase_configured(admin=True):
        return
    try:
        client = get_admin_client()
        rows = []
        for rank, chunk in enumerate(chunks, start=1):
            rows.append(
                {
                    "query": query,
                    "disease_layer": layer,
                    "chunk_id": chunk.get("chunk_id"),
                    "rank": rank,
                    "similarity": chunk.get("similarity"),
                    "section": chunk.get("section_title"),
                    "page": chunk.get("page_start"),
                    "created_at": utc_now_iso(),
                }
            )
        if rows:
            client.table("retrieval_logs").insert(rows).execute()
    except Exception:
        return
