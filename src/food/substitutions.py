from __future__ import annotations

from src.retrieval.scoring import keyword_overlap_score


SUBSTITUTION_RULES = [
    (("juice", "sugary drink", "soda", "sweetened beverage"), ["water", "no-calorie beverage", "whole fruit when the retrieved evidence supports fruit intake"]),
    (("refined grain", "white rice", "white bread"), ["whole grains when supported by retrieved evidence"]),
    (("processed food", "ultraprocessed"), ["minimally processed whole foods"]),
    (("high sodium", "salt", "salty"), ["herbs/spices instead of salt-containing preparations"]),
    (("red meat", "processed meat", "sausage", "bacon"), ["lean proteins", "plant-based protein when evidence supports it"]),
]


def suggest_substitutions(query: str, chunks: list[dict]) -> list[dict]:
    evidence = " ".join(c.get("content", "") for c in chunks)
    suggestions: list[dict] = []
    q = (query or "").lower()
    for triggers, alternatives in SUBSTITUTION_RULES:
        if not any(t in q for t in triggers):
            continue
        for alt in alternatives:
            support = keyword_overlap_score(alt, evidence)
            matched = [c for c in chunks if keyword_overlap_score(alt, c.get("content", "")) > 0]
            if support > 0 and matched:
                chunk = matched[0]
                suggestions.append(
                    {
                        "instead_of": ", ".join(triggers),
                        "alternative": alt,
                        "evidence_chunk_id": chunk.get("chunk_id"),
                        "citation_label": chunk.get("citation_label"),
                    }
                )
    return suggestions
