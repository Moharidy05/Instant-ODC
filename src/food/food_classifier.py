from __future__ import annotations


def classify_food_guidance(query: str, chunks: list[dict], safety_result: dict | None = None) -> str:
    if safety_result and safety_result.get("safety_label") == "refuse":
        return "refused"
    evidence = " ".join(c.get("content", "") for c in chunks).lower()
    q = (query or "").lower()
    if not chunks:
        return "not_supported_by_retrieved_evidence"
    encouraged_terms = ("encourage", "recommended", "vegetables", "fruits", "legumes", "whole grains", "nuts", "seeds", "fiber", "water")
    limit_terms = ("limit", "minimize", "avoid", "sugar-sweetened", "sugary", "refined", "processed", "sodium", "red meat", "processed meat")
    caution_terms = ("caution", "individual", "keto", "ketogenic", "alcohol", "nonnutritive", "saturated")
    if any(term in q or term in evidence for term in limit_terms):
        return "better_to_limit"
    if any(term in q or term in evidence for term in caution_terms):
        return "suitable_with_caution"
    if any(term in q or term in evidence for term in encouraged_terms):
        return "encouraged"
    return "not_supported_by_retrieved_evidence"
