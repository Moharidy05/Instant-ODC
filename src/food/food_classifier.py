from __future__ import annotations

from src.retrieval.scoring import keyword_overlap_score


def _has_evidence(evidence: str, terms: tuple[str, ...]) -> bool:
    return any(term in evidence for term in terms)


def classify_food_guidance(query: str, chunks: list[dict], safety_result: dict | None = None) -> str:
    if safety_result and safety_result.get("safety_label") == "refuse":
        return "refused"
    evidence = " ".join(c.get("content", "") for c in chunks).lower()
    q = (query or "").lower()
    if not chunks:
        return "not_supported_by_retrieved_evidence"
    if keyword_overlap_score(query, evidence) == 0:
        return "not_supported_by_retrieved_evidence"

    exact_or_personal = ("grams", "portion", "daily", "every day", "my ", "i have")
    if any(term in q for term in exact_or_personal):
        return "suitable_with_caution"

    if any(term in q for term in ("soda", "sugary drink", "sugar-sweetened", "juice drink", "orange juice", "fruit juice", "juice")):
        if _has_evidence(evidence, ("sugar-sweetened", "juice", "beverage", "water", "added sugar")):
            return "better_to_limit"

    if "water" in q:
        if _has_evidence(evidence, ("water", "sugar-sweetened", "beverage")):
            return "encouraged"

    if any(term in q for term in ("legumes", "legume", "beans", "bean", "lentils", "lentil")):
        if _has_evidence(evidence, ("legumes", "beans", "lentils", "plant protein", "fiber")):
            return "encouraged"

    if any(term in q for term in ("processed foods", "processed food", "refined grains", "sweets", "sweet")):
        if _has_evidence(evidence, ("processed", "refined", "added sugar", "sodium", "minimize", "limit")):
            return "better_to_limit"

    if any(term in q for term in ("whole grains", "whole grain")):
        if _has_evidence(evidence, ("whole grains", "fiber", "carbohydrate")):
            return "encouraged"

    if any(term in q for term in ("fruit", "fruits")):
        if _has_evidence(evidence, ("fruits", "fruit", "fiber", "no added sugar")):
            return "encouraged"

    caution_terms = ("keto", "ketogenic", "alcohol", "nonnutritive", "saturated", "very low carbohydrate")
    if any(term in q for term in caution_terms):
        return "suitable_with_caution"

    limit_terms = ("sugar-sweetened", "sugary", "refined", "processed", "sodium", "red meat", "processed meat", "limit", "minimize")
    encouraged_terms = ("encourage", "recommended", "vegetables", "fruits", "legumes", "whole grains", "nuts", "seeds", "fiber", "water")
    if any(term in q for term in limit_terms) and _has_evidence(evidence, limit_terms):
        return "better_to_limit"
    if any(term in q for term in encouraged_terms) and _has_evidence(evidence, encouraged_terms):
        return "encouraged"
    return "not_supported_by_retrieved_evidence"
