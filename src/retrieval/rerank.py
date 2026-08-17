from __future__ import annotations

from src.retrieval.scoring import keyword_overlap_score


def rerank_chunks(query: str, chunks: list[dict], top_k: int) -> list[dict]:
    scored: list[dict] = []
    for chunk in chunks:
        lexical = keyword_overlap_score(query, chunk.get("content", ""))
        base = float(chunk.get("similarity", 0.0) or 0.0)
        item = dict(chunk)
        item["rerank_score"] = round((0.75 * base) + (0.25 * lexical), 6)
        scored.append(item)
    return sorted(scored, key=lambda x: x.get("rerank_score", x.get("similarity", 0)), reverse=True)[:top_k]
