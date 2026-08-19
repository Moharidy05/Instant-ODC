from __future__ import annotations

import re


SAFETY_NOTE = (
    "This is not a personalized diet plan or medical prescription. "
    "For individualized nutrition therapy, consult a qualified clinician or registered dietitian."
)

REFUSE_PATTERNS = [
    (r"(insulin dosing|how much insulin|insulin should i take)", "Query asks for insulin dosing."),
    (r"(medication adjustment|adjust.*medication|change my dose|change.*medication)", "Query asks for medication adjustment."),
    (r"(emergency treatment|emergency|severe hypoglycemia|ketoacidosis|what should i do right now)", "Query asks for emergency treatment."),
    (r"(full meal plan|meal plan).*(exact grams|grams|calories)", "Query asks for a full meal plan with exact quantities."),
    (r"(diagnose me|personal diagnosis|do i have diabetes)", "Query asks for personal diagnosis."),
]

COMORBIDITY_PATTERNS = [
    (r"(kidney disease|renal|ckd)", "kidney disease"),
    (r"(cardiovascular|heart disease|cvd)", "cardiovascular disease"),
    (r"pregnancy|pregnant", "pregnancy"),
    (r"hypertension|high blood pressure", "hypertension"),
]

CAUTION_PATTERNS = [
    (r"(\d+\s*grams|exact amount|specific amount)", "Query asks for exact quantities that this navigator does not prescribe."),
    (r"(sglt2|keto|ketogenic|very low carbohydrate|nonnutritive sweetener|alcohol)", "Query involves a dietary pattern, alcohol, sweetener, or medication context requiring cautious guideline-grounded response."),
    (r"(my condition|my diagnosis|i have)", "Query mentions personal health context."),
]

SCOPE_PATTERNS = [
    r"diabet",
    r"\bfood(s)?\b",
    r"\bdrink(s)?\b",
    r"\bbeverage(s)?\b",
    r"\bnutrition(al)?\b",
    r"\bdiet(ary)?\b",
    r"\beat(ing)?\b",
    r"\bcarb(ohydrate)?s?\b",
    r"\bfiber\b",
    r"\bprotein\b",
    r"\bfat(s)?\b",
    r"\bsodium\b",
    r"\bsalt\b",
    r"\bfruit(s)?\b",
    r"\bvegetable(s)?\b",
    r"\blegume(s)?\b",
    r"\bbeans?\b",
    r"\blentils?\b",
    r"\bwhole grains?\b",
    r"\bsugar(y)?\b",
    r"\bjuice(s)?\b",
    r"\bsoda\b",
    r"\bsoft drink(s)?\b",
    r"\bwater\b",
    r"\bprocessed foods?\b",
    r"\bultra-processed\b",
    r"\brefined grains?\b",
    r"\bsweets?\b",
    r"\beating patterns?\b",
]


def _in_scope(query_lower: str) -> bool:
    return any(re.search(pattern, query_lower) for pattern in SCOPE_PATTERNS)


def classify_query(query: str, active_layer: str = "diabetes") -> dict:
    query_lower = (query or "").lower()

    for pattern, reason in REFUSE_PATTERNS:
        if re.search(pattern, query_lower):
            return {"safety_label": "refuse", "reason": reason, "recommended_action": "refuse_and_explain"}

    for pattern, comorbidity in COMORBIDITY_PATTERNS:
        if re.search(pattern, query_lower) and active_layer == "diabetes":
            return {
                "safety_label": "refuse",
                "reason": f"The {comorbidity} guideline layer is not active/indexed, so diabetes-only evidence cannot answer comorbidity-specific advice.",
                "recommended_action": "refuse_and_explain",
            }

    for pattern, reason in CAUTION_PATTERNS:
        if re.search(pattern, query_lower):
            return {"safety_label": "needs_caution", "reason": reason, "recommended_action": "answer_with_caution"}

    if not _in_scope(query_lower):
        return {
            "safety_label": "refuse",
            "reason": "Query is outside the diabetes food safety navigator scope.",
            "recommended_action": "refuse_and_explain",
        }

    return {
        "safety_label": "allowed",
        "reason": "Query appears to be a general food/beverage safety question.",
        "recommended_action": "answer_with_evidence",
    }
