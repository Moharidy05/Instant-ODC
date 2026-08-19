from __future__ import annotations

from src.ai.generation import generate_text
from src.answering.citation_validator import validate_citations
from src.answering.prompts import (
    INSUFFICIENT_EVIDENCE_TEMPLATE,
    REFUSE_TEMPLATE,
    STRICT_REGEN_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from src.core.config import MIN_RETRIEVAL_CONFIDENCE, PROJECT_TOPIC, RETRIEVAL_TOP_K
from src.core.errors import ConfigurationError, ModelFallbackExhausted
from src.food.food_classifier import classify_food_guidance
from src.food.substitutions import suggest_substitutions
from src.layers.disease_layer_orchestrator import orchestrate_disease_layer
from src.retrieval.retrieve import retrieve_chunks
from src.safety.confidence import retrieval_confidence
from src.safety.safety import SAFETY_NOTE, classify_query
from src.safety.unsupported_claims import find_unsupported_claims


def format_evidence_chunks(chunks: list[dict]) -> str:
    parts = []
    for idx, chunk in enumerate(chunks, start=1):
        parts.append(
            "\n".join(
                [
                    f"Chunk {idx}",
                    f"chunk_id: {chunk.get('chunk_id', '')}",
                    f"document: {chunk.get('document_title', '')}",
                    f"section: {chunk.get('section_title', '')}",
                    f"page: {chunk.get('page_start', '')}",
                    f"citation_label: {chunk.get('citation_label', '')}",
                    f"similarity: {chunk.get('similarity', 0)}",
                    f"content: {chunk.get('content', '')}",
                ]
            )
        )
    return "\n\n".join(parts)


def generate_answer(
    query: str,
    chunks: list[dict],
    safety_result: dict,
    *,
    min_confidence: float = MIN_RETRIEVAL_CONFIDENCE,
) -> str:
    if safety_result.get("safety_label") == "refuse":
        return REFUSE_TEMPLATE.format(reason=safety_result.get("reason", "Request is outside scope."), safety_note=SAFETY_NOTE)

    confidence = retrieval_confidence(chunks, min_confidence, query=query)
    if not confidence["can_answer"]:
        return INSUFFICIENT_EVIDENCE_TEMPLATE.format(
            top_similarity=confidence["top_similarity"],
            threshold=confidence["threshold"],
            safety_note=SAFETY_NOTE,
        )

    evidence = format_evidence_chunks(chunks)
    prompt = USER_PROMPT_TEMPLATE.format(query=query, evidence_chunks=evidence)
    try:
        answer = generate_text(prompt, SYSTEM_PROMPT, temperature=0.2)
        unsupported = find_unsupported_claims(answer, chunks)
        if unsupported:
            stricter = STRICT_REGEN_PROMPT_TEMPLATE.format(
                query=query,
                evidence_chunks=evidence,
                unsupported_claims="\n".join(u["sentence"] for u in unsupported[:6]),
            )
            answer = generate_text(stricter, SYSTEM_PROMPT, temperature=0.1)
        return answer
    except (ConfigurationError, ModelFallbackExhausted, Exception):
        return deterministic_answer(query, chunks, safety_result)


def deterministic_answer(query: str, chunks: list[dict], safety_result: dict) -> str:
    classification = classify_food_guidance(query, chunks, safety_result)
    top = chunks[0] if chunks else {}
    excerpt = (top.get("content", "") or "")[:450].strip()
    citation = (
        f"{top.get('document_title', 'Unknown document')}; "
        f"{top.get('section_title', 'Unknown section')}; "
        f"page {top.get('page_start', 'N/A')}; "
        f"chunk ID {top.get('chunk_id', 'N/A')}"
        if top
        else "No citation available."
    )
    alternatives = suggest_substitutions(query, chunks)
    alt_text = "; ".join(a["alternative"] for a in alternatives) if alternatives else "No evidence-tied alternative identified from the retrieved chunks."
    return f"""Food Safety Classification:
{classification}

Short Answer:
The answer should be interpreted only within the retrieved ADA diabetes nutrition evidence.

Why:
The retrieved evidence discusses this topic in the context of diabetes nutrition recommendations. Avoid treating this as personalized medical advice.

Better Alternative:
{alt_text}

Evidence Excerpt:
{excerpt}

Citations:
{citation}

Safety Note:
{SAFETY_NOTE}
"""


def full_pipeline(
    query: str,
    clinical_topic: str = PROJECT_TOPIC,
    disease_layer: str = "diabetes",
    top_k: int = RETRIEVAL_TOP_K,
) -> dict:
    layer = orchestrate_disease_layer(query, disease_layer)
    safety = classify_query(query, active_layer=layer["effective_layer"] if layer["can_answer"] else "diabetes")
    if not layer["can_answer"] and safety.get("safety_label") != "refuse":
        safety = {
            "safety_label": "refuse",
            "reason": layer["reason"],
            "recommended_action": "refuse_and_explain",
        }
    chunks: list[dict] = []
    if safety["safety_label"] != "refuse":
        filters = layer["retrieval_filters"]
        chunks = retrieve_chunks(query, filters.get("clinical_topic", clinical_topic), filters.get("disease_layer", disease_layer), top_k)
    answer = generate_answer(query, chunks, safety)
    citation_check = validate_citations(answer, chunks) if chunks else {"valid": safety["safety_label"] == "refuse", "failures": []}
    unsupported_claims = find_unsupported_claims(answer, chunks) if chunks else []
    return {
        "query": query,
        "layer": layer,
        "safety_result": safety,
        "chunks": chunks,
        "confidence": retrieval_confidence(chunks, query=query),
        "answer": answer,
        "citation_validation": citation_check,
        "substitutions": suggest_substitutions(query, chunks),
        "unsupported_claims": unsupported_claims,
    }
