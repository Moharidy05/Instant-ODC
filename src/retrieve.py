"""
Retrieval module for the Diabetes Food Safety RAG pipeline.
============================================================

Embeds a user query with Google Gemini, then calls the Supabase RPC
function ``match_guideline_chunks`` for cosine-similarity vector search.

Can be used as an imported function or run directly:
    python -m src.retrieve "Is brown rice good for diabetes?"
"""

import sys

from src.supabase_client import get_client
from src.embeddings import embed_text


def retrieve_chunks(
    query: str,
    clinical_topic: str = "diabetes_food_safety",
    disease_layer: str = "diabetes",
    top_k: int = 5,
) -> list[dict]:
    """Retrieve the most relevant guideline chunks for a query.

    Args:
        query:           The user's natural-language question.
        clinical_topic:  Filter by clinical topic (default: diabetes_food_safety).
        disease_layer:   Filter by disease layer   (default: diabetes).
        top_k:           Number of chunks to return.

    Returns:
        A list of dicts, each containing chunk_id, content, section_title,
        page_start, page_end, citation_label, chunk_type, disease_layer,
        and similarity score.
    """
    # Embed the query with the "query" task type for asymmetric retrieval
    query_embedding = embed_text(query, kind="query")

    # Call the Supabase RPC function defined in sql/003_match_chunks_function.sql
    client = get_client()
    response = client.rpc(
        "match_guideline_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_clinical_topic": clinical_topic,
            "filter_disease_layer": disease_layer,
        },
    ).execute()

    return response.data


# ──────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Is it safe to eat fruit?"
    print(f"Retrieving chunks for query: '{query}'\n")

    results = retrieve_chunks(query)

    if not results:
        print("No chunks found.")

    for res in results:
        similarity = res.get("similarity", 0)
        section = res.get("section_title", "Unknown Section")
        pages = f"p.{res.get('page_start', '?')}-{res.get('page_end', '?')}"
        content = res.get("content", "")

        print(f"--- Similarity: {similarity:.4f} | {section} ({pages}) ---")
        print(f"{content[:200]}...\n")
