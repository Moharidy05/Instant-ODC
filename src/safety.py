import re

REFUSE_PATTERNS = [
    (r"(insulin dosing|how much insulin)", "Query mentions insulin dosing."),
    (r"(medication adjustment|adjust my medication)", "Query mentions medication adjustment."),
    (r"emergency treatment", "Query mentions emergency treatment."),
    (r"full meal plan.*grams", "Query asks for a full meal plan with exact grams."),
    (r"personal medical diagnosis", "Query mentions personal medical diagnosis."),
    (r"drug interaction", "Query mentions drug interactions."),
    (r"(kidney disease|renal)", "The guideline for this comorbidity (kidney disease) hasn't been loaded yet."),
    (r"(cardiovascular|heart disease)", "The guideline for this comorbidity (cardiovascular/heart disease) hasn't been loaded yet."),
    (r"pregnancy", "The guideline for this comorbidity (pregnancy) hasn't been loaded yet."),
    (r"hypertension", "The guideline for this comorbidity (hypertension) hasn't been loaded yet.")
]

CAUTION_PATTERNS = [
    (r"(\d+\s*grams|specific amount)", "Query asks for specific gram amounts."),
    (r"(my condition|my diagnosis|i have)", "Query mentions a specific personal condition."),
    (r"(exotic|rare food)", "Query asks about a very specific food not likely covered in guidelines.")
]

def classify_query(query: str) -> dict:
    """
    Classify a user query into safety categories.
    """
    query_lower = query.lower()
    
    # Check for refusals
    for pattern, reason in REFUSE_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "safety_label": "refuse",
                "reason": reason,
                "recommended_action": "refuse_and_explain"
            }
            
    # Check for cautions
    for pattern, reason in CAUTION_PATTERNS:
        if re.search(pattern, query_lower):
            return {
                "safety_label": "needs_caution",
                "reason": reason,
                "recommended_action": "answer_with_caution"
            }
            
    # Default to allowed
    return {
        "safety_label": "allowed",
        "reason": "Query appears to be a general food/beverage safety question.",
        "recommended_action": "answer_with_evidence"
    }
