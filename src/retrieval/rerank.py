from __future__ import annotations

from src.retrieval.scoring import keyword_overlap_score


LOW_VALUE_CHUNK_TYPES = {"citation_or_license"}
LOW_VALUE_SECTION_TERMS = ("references", "reference list", "bibliography", "license", "copyright")
BEVERAGE_QUERY_TERMS = ("juice", "soda", "soft drink", "sugary drink", "sugar-sweetened", "beverage", "water")
BEVERAGE_BOOST_TERMS = ("juice", "sugar-sweetened", "beverage", "water", "soda", "fruit")
LOW_VALUE_TOPIC_TERMS = ("alcohol", "fasting", "smoking", "references")


def is_low_value_chunk(chunk: dict) -> bool:
    chunk_type = str(chunk.get("chunk_type", "") or "").strip().lower()
    section = str(chunk.get("section_title", "") or "").strip().lower()
    content = str(chunk.get("content", "") or "").strip().lower()
    if chunk_type in LOW_VALUE_CHUNK_TYPES:
        return True
    if any(term in section for term in LOW_VALUE_SECTION_TERMS):
        return True
    if content.startswith("references") or content.startswith("reference "):
        return True
    return False


def rerank_chunks(query: str, chunks: list[dict], top_k: int, expanded_query: str | None = None) -> list[dict]:
    query_lower = (query or "").lower()
    expanded = expanded_query or query
    beverage_query = any(term in query_lower for term in BEVERAGE_QUERY_TERMS)
    low_value_query = any(term in query_lower for term in LOW_VALUE_TOPIC_TERMS)
    scored: list[dict] = []
    for chunk in chunks:
        text = " ".join(
            str(chunk.get(field, "") or "")
            for field in ("section_title", "chunk_type", "content", "citation_label")
        )
        text_lower = text.lower()
        lexical = keyword_overlap_score(query, text)
        expanded_lexical = keyword_overlap_score(expanded, text)
        base = float(chunk.get("similarity", 0.0) or 0.0)
        metadata_boost = 0.0
        if lexical > 0:
            metadata_boost += 0.03
        if keyword_overlap_score(query, str(chunk.get("section_title", "") or "")) > 0:
            metadata_boost += 0.04
        chunk_type = str(chunk.get("chunk_type", "") or "").lower()
        if chunk_type in {"recommendation", "guideline_recommendation", "nutrition_guidance"}:
            metadata_boost += 0.03
        if beverage_query and any(term in text_lower for term in BEVERAGE_BOOST_TERMS):
            metadata_boost += 0.09
        if is_low_value_chunk(chunk) and not low_value_query:
            metadata_boost -= 0.35
        if not low_value_query and any(term in text_lower for term in ("alcohol", "fasting", "smoking")):
            metadata_boost -= 0.04
        item = dict(chunk)
        item["lexical_overlap"] = round(lexical, 4)
        item["expanded_lexical_overlap"] = round(expanded_lexical, 4)
        item["rerank_score"] = round((0.58 * base) + (0.24 * lexical) + (0.18 * expanded_lexical) + metadata_boost, 6)
        scored.append(item)
    ordered = sorted(scored, key=lambda x: x.get("rerank_score", x.get("similarity", 0)), reverse=True)
    filtered = [chunk for chunk in ordered if not is_low_value_chunk(chunk)]
    return (filtered or ordered)[:top_k]
