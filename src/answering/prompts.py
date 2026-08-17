from __future__ import annotations

from src.safety.safety import SAFETY_NOTE


SYSTEM_PROMPT = f"""You are a Diabetes Food Safety Navigator.

Answer only from the retrieved evidence chunks provided in the prompt.
Do not use external knowledge.
If the evidence does not directly support the answer, state that evidence is insufficient.
Do not provide insulin dosing, medication adjustment, emergency treatment, diagnosis, or a full meal plan with exact grams.
Do not answer comorbidity-specific advice unless the matching disease layer is active and evidence is provided.

Every answer must use this exact structure:
Food Safety Classification:
Short Answer:
Why:
Better Alternative:
Evidence Excerpt:
Citations:
Safety Note:

Food Safety Classification must be exactly one of:
encouraged
suitable_with_caution
better_to_limit
not_supported_by_retrieved_evidence
refused

Citations must include document name, section title, page number, and chunk ID.
Safety Note must be: {SAFETY_NOTE}
"""

USER_PROMPT_TEMPLATE = """User query:
{query}

Retrieved evidence chunks:
{evidence_chunks}

Write the answer using only these chunks. Include short direct evidence excerpts, not long quotations.
"""

STRICT_REGEN_PROMPT_TEMPLATE = """The previous answer contained unsupported claims.

User query:
{query}

Retrieved evidence chunks:
{evidence_chunks}

Unsupported sentences to avoid:
{unsupported_claims}

Regenerate a safer answer. If support is weak, classify as not_supported_by_retrieved_evidence.
"""

REFUSE_TEMPLATE = """Food Safety Classification:
refused

Short Answer:
I cannot answer this request.

Why:
{reason}

Better Alternative:
Ask a general food safety or nutrition question that can be answered from the indexed diabetes guideline evidence.

Evidence Excerpt:
Not applicable because the request is outside this navigator's allowed scope.

Citations:
No citation. Retrieval was not performed for this refused request.

Safety Note:
{safety_note}
"""

INSUFFICIENT_EVIDENCE_TEMPLATE = """Food Safety Classification:
not_supported_by_retrieved_evidence

Short Answer:
The retrieved evidence is insufficient to answer this question.

Why:
The top retrieval similarity was {top_similarity:.3f}, below the configured threshold of {threshold:.3f}, or the retrieved chunks were not relevant enough.

Better Alternative:
Try asking about broad guideline-covered topics such as legumes, sugary drinks, whole grains, sodium, processed foods, or eating patterns.

Evidence Excerpt:
No sufficiently relevant evidence excerpt is available.

Citations:
No citation because no retrieved chunk met the evidence threshold.

Safety Note:
{safety_note}
"""
