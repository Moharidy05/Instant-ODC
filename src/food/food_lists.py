from __future__ import annotations


DEFAULT_GUIDANCE = {
    "encouraged": [
        ("legumes", "Evidence commonly appears in nutrition behavior/recommendation chunks."),
        ("whole grains", "Evidence commonly appears in carbohydrate/fiber guidance chunks."),
        ("vegetables", "Evidence commonly appears in eating pattern guidance chunks."),
        ("water", "Evidence commonly appears in beverage guidance chunks."),
    ],
    "suitable_with_caution": [
        ("ketogenic diet", "Requires careful evidence and clinical context."),
        ("nonnutritive sweeteners", "Guideline context should be shown before advising."),
        ("alcohol", "Requires safety caveats if evidence exists."),
    ],
    "better_to_limit": [
        ("sugar-sweetened beverages", "Evidence commonly supports reducing sugary drinks."),
        ("refined grains", "Evidence commonly supports preferring whole grains."),
        ("processed foods", "Evidence commonly supports minimally processed patterns."),
        ("high-sodium foods", "Evidence commonly supports sodium reduction."),
        ("red/processed meat", "Evidence commonly supports alternative protein patterns."),
    ],
}


def build_food_guidance_lists(chunks: list[dict]) -> dict[str, list[dict]]:
    evidence = " ".join(c.get("content", "").lower() for c in chunks)
    output: dict[str, list[dict]] = {k: [] for k in DEFAULT_GUIDANCE}
    for category, items in DEFAULT_GUIDANCE.items():
        for food, note in items:
            supporting = [c for c in chunks if any(tok in c.get("content", "").lower() for tok in food.split("/"))]
            if not supporting and food not in evidence:
                continue
            chunk = supporting[0] if supporting else (chunks[0] if chunks else {})
            output[category].append(
                {
                    "food": food,
                    "note": note,
                    "evidence_chunk_id": chunk.get("chunk_id", ""),
                    "citation_label": chunk.get("citation_label", ""),
                }
            )
    return output
