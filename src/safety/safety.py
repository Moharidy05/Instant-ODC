from __future__ import annotations

import re


SAFETY_NOTE = (
    "This navigator provides guideline-grounded educational information "
    "and is not a personalized medical prescription."
)


REFUSE_PATTERNS = [
    (
        r"(insulin dosing|how much insulin|insulin should i take|"
        r"increase my insulin|decrease my insulin)",
        "Query asks for insulin dosing.",
    ),
    (
        r"(medication adjustment|adjust.*medication|change my dose|"
        r"change.*medication|stop.*medication|increase my dose|decrease my dose)",
        "Query asks for medication adjustment.",
    ),
    (
        r"(emergency treatment|severe hypoglycemia|ketoacidosis|"
        r"what should i do right now|sugar is crashing|very low sugar)",
        "Query asks for emergency treatment.",
    ),
    (
        r"(diagnose me|personal diagnosis|do i have diabetes)",
        "Query asks for personal diagnosis.",
    ),
    (
        r"(full meal plan|meal plan).*(exact grams|grams|calories)",
        "Query asks for a full personalized meal plan with exact quantities.",
    ),
]


CAUTION_PATTERNS = [
    (
        r"(\d+\s*grams|\d+\s*g\b|exact amount|specific amount|"
        r"how many grams|how much rice|how much bread)",
        "Query asks for exact food quantities.",
    ),
    (
        r"(alcohol|ketogenic|very low carbohydrate|sglt2)",
        "Query involves a context requiring cautious guideline-grounded advice.",
    ),
]


SCOPE_PATTERNS = [
    r"(diabetes|diabetic|prediabetes|blood sugar|glucose|a1c)",
    r"(food|eat|drink|nutrition|diet|meal|beverage)",
    r"(carb|carbohydrate|protein|fat|fiber|sodium|salt)",
    r"(juice|soda|water|fruit|banana|apple|orange)",
    r"(rice|bread|pasta|vegetable|legume|bean|lentil|nuts)",
    r"(processed food|whole grain|sweetener|mediterranean)",
    r"(kidney|renal|ckd|dialysis)",
    r"(heart|cardiovascular|cvd|hypertension)",
    r"(diabetic foot|foot ulcer|foot wound|offloading)",
    r"(masld|nafld|fatty liver|hepatic)",
]


def _matches_any(patterns: list[str], query: str) -> bool:
    return any(
        re.search(pattern, query, flags=re.IGNORECASE)
        for pattern in patterns
    )


def classify_query(
    query: str,
    active_layer: str = "diabetes",
) -> dict:
    del active_layer
    query = (query or "").strip()

    if not query:
        return {
            "safety_label": "refuse",
            "reason": "Empty query.",
            "recommended_action": "refuse_and_explain",
        }

    for pattern, reason in REFUSE_PATTERNS:
        if re.search(pattern, query, flags=re.IGNORECASE):
            return {
                "safety_label": "refuse",
                "reason": reason,
                "recommended_action": "refuse_and_explain",
            }

    if not _matches_any(SCOPE_PATTERNS, query):
        return {
            "safety_label": "refuse",
            "reason": (
                "Query is outside the diabetes guideline navigator scope."
            ),
            "recommended_action": "refuse_and_explain",
        }

    for pattern, reason in CAUTION_PATTERNS:
        if re.search(pattern, query, flags=re.IGNORECASE):
            return {
                "safety_label": "needs_caution",
                "reason": reason,
                "recommended_action": "answer_with_caution",
            }

    return {
        "safety_label": "allowed",
        "reason": (
            "Query is eligible for guideline routing and evidence retrieval."
        ),
        "recommended_action": "answer_with_evidence",
    }

