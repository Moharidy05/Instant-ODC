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


def expand_retrieval_query(query: str) -> str:
    q = (query or "").lower()
    expansions: list[str] = []
    if any(term in q for term in ("orange juice", "juice", "fruit juice")):
        expansions.append(
            "sugar-sweetened beverages juice drinks nutritive sweeteners water replace beverages whole fruit fruit no added sugar"
        )
    if any(term in q for term in ("soda", "soft drink", "sugary drink")):
        expansions.append(
            "sugar-sweetened beverages regular soda pop water nonnutritive sweeteners added sugar beverages"
        )
    if "water" in q:
        expansions.append("water beverage sugar-sweetened beverages no-calorie beverage")
    if any(term in q for term in ("legumes", "legume", "beans", "bean", "lentils", "lentil")):
        expansions.append("legumes dried beans peas lentils plant protein fiber eating pattern")
    if "processed foods" in q or "processed food" in q:
        expansions.append("processed foods ultra-processed foods refined grains added sugar sodium minimally processed foods")
    if "whole grains" in q or "whole grain" in q:
        expansions.append("whole grains fiber high-quality carbohydrates minimally processed nutrient-dense")
    if "fruit" in q:
        expansions.append("fruits whole fruits fresh frozen canned no added sugar fiber")
    return query if not expansions else query + "\n" + " ".join(expansions)


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
    expanded_query = expand_retrieval_query(query)

    if not supabase_configured(admin=False):
        return local_retrieve_chunks(query, clinical_topic, disease_layer, top_k, expanded_query=expanded_query)

    try:
        query_embedding = embed_text(expanded_query, kind="query")
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
        results = rerank_chunks(query, candidates, top_k, expanded_query=expanded_query)
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
    expanded_query: str | None = None,
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
            text = " ".join(
                str(chunk.get(field, ""))
                for field in ("section_title", "chunk_type", "content", "citation_label")
            )
            score = max(
                lexical_similarity(query, text),
                lexical_similarity(expanded_query or query, text),
            )
            item = dict(chunk)
            item["similarity"] = round(score, 4)
            rows.append(item)
    return rerank_chunks(query, rows, top_k, expanded_query=expanded_query or query)


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
