from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "for", "from", "have", "i",
    "in", "is", "it", "me", "my", "of", "on", "or", "should", "the", "this", "to",
    "with", "what", "when", "where", "who", "why", "how", "person", "people", "diabetes",
}


def keywords(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower()) if t not in STOPWORDS}


def keyword_overlap_score(query: str, text: str) -> float:
    q = keywords(query)
    if not q:
        return 0.0
    t = keywords(text)
    return len(q & t) / len(q)


def lexical_similarity(query: str, text: str) -> float:
    q_terms = Counter(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", query.lower()))
    t_terms = Counter(re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower()))
    if not q_terms or not t_terms:
        return 0.0
    overlap = sum(min(q_terms[k], t_terms[k]) for k in q_terms)
    return min(1.0, overlap / max(1, sum(q_terms.values())))


def precision_at_k(results: list[dict], expected_topic: str, k: int) -> float:
    if k <= 0:
        return 0.0
    top = results[:k]
    if not top:
        return 0.0
    topic_terms = keywords(expected_topic)
    if not topic_terms:
        return 0.0
    relevant = 0
    for chunk in top:
        haystack = " ".join(
            str(chunk.get(field, ""))
            for field in ("section_title", "content", "chunk_type", "citation_label")
        ).lower()
        if topic_terms & keywords(haystack):
            relevant += 1
    return relevant / len(top)


def average_similarity(results: list[dict]) -> float:
    if not results:
        return 0.0
    return sum(float(r.get("similarity", 0.0)) for r in results) / len(results)
