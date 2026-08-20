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
from src.layers.disease_layer_orchestrator import resolve_disease_layer
from src.retrieval.confidence import evaluate_retrieval_confidence
from src.retrieval.retrieve import retrieve_chunks
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
        return REFUSE_TEMPLATE.format(
            reason=safety_result.get("reason", "Request is outside scope."),
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
    alt_text = (
        "; ".join(a["alternative"] for a in alternatives)
        if alternatives
        else "No evidence-tied alternative identified from the retrieved chunks."
    )
    return f"""Food Safety Classification:
{classification}

Short Answer:
The answer should be interpreted only within the retrieved guideline evidence.

Why:
The retrieved evidence discusses this topic in the context of clinical guideline recommendations. Avoid treating this as personalized medical advice.

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
    clinical_topic: str | None = None,
    disease_layer: str = "auto",
    top_k: int = RETRIEVAL_TOP_K,
) -> dict:
    query = (query or "").strip()

    safety = classify_query(query)

    if safety["safety_label"] == "refuse":
        return {
            "question": query,
            "query": query,
            "layer": {
                "effective_layer": None,
                "active": False,
                "can_answer": False,
                "reason": safety["reason"],
            },
            "safety": safety,
            "safety_result": safety,
            "confidence": {
                "status": "not_evaluated",
                "can_answer": False,
            },
            "retrieval": {
                "confidence": "not_evaluated",
                "top_score": 0.0,
                "chunks": [],
            },
            "chunks": [],
            "answer": {
                "classification": "refused",
                "short_answer": safety["reason"],
                "reason": safety["reason"],
                "safer_alternative": None,
                "citations": [],
            },
            "substitutions": [],
            "citation_validation": {
                "valid": True,
                "reason": "No citation required for safety refusal.",
                "cited_chunk_ids": [],
            },
            "unsupported_claims": [],
        }

    route = resolve_disease_layer(
        query=query,
        requested_layer=disease_layer or "auto",
    )

    if not route["can_answer"]:
        return {
            "question": query,
            "query": query,
            "layer": {
                **route,
                "active": False,
            },
            "safety": safety,
            "safety_result": safety,
            "confidence": {
                "status": "not_evaluated",
                "can_answer": False,
            },
            "retrieval": {
                "confidence": "not_evaluated",
                "top_score": 0.0,
                "chunks": [],
            },
            "chunks": [],
            "answer": {
                "classification": "not_supported_by_retrieved_evidence",
                "short_answer": route["reason"],
                "reason": route["reason"],
                "safer_alternative": None,
                "citations": [],
            },
            "substitutions": [],
            "citation_validation": {
                "valid": True,
                "reason": "No citation required because no guideline layer was selected.",
                "cited_chunk_ids": [],
            },
            "unsupported_claims": [],
        }

    effective_layer = route["effective_layer"]
    effective_topic = clinical_topic or route["clinical_topic"]
    allowed_document_ids = route["allowed_document_ids"]

    chunks = retrieve_chunks(
        query=query,
        clinical_topic=effective_topic,
        disease_layer=effective_layer,
        top_k=top_k,
        allowed_document_ids=allowed_document_ids,
    )

    confidence = evaluate_retrieval_confidence(
        query=query,
        chunks=chunks,
        expected_layer=effective_layer,
    )

    if not confidence["can_answer"]:
        return {
            "question": query,
            "query": query,
            "layer": {
                "effective_layer": effective_layer,
                "active": True,
                "clinical_topic": effective_topic,
                "allowed_document_ids": allowed_document_ids,
                "can_answer": True,
                "route_status": route["route_status"],
                "reason": route["reason"],
            },
            "safety": safety,
            "safety_result": safety,
            "confidence": confidence,
            "retrieval": {
                "confidence": confidence["status"],
                "top_score": confidence["top_similarity"],
                "chunks": chunks,
            },
            "chunks": chunks,
            "answer": {
                "classification": "not_supported_by_retrieved_evidence",
                "short_answer": "The retrieved evidence is insufficient to answer this question.",
                "reason": f"Top similarity was {confidence['top_similarity']:.3f} and composite score was {confidence['composite_score']:.3f}.",
                "safer_alternative": None,
                "citations": [],
            },
            "substitutions": [],
            "citation_validation": {
                "valid": True,
                "reason": "No citations generated for insufficient evidence.",
                "cited_chunk_ids": [],
            },
            "unsupported_claims": [],
        }

    answer = generate_answer(query, chunks, safety)
    citation_check = (
        validate_citations(answer, chunks)
        if chunks
        else {"valid": True, "failures": []}
    )
    unsupported_claims = (
        find_unsupported_claims(answer, chunks)
        if chunks
        else []
    )
    substitutions = suggest_substitutions(query, chunks)

    return {
        "question": query,
        "query": query,
        "layer": {
            "effective_layer": effective_layer,
            "active": True,
            "clinical_topic": effective_topic,
            "allowed_document_ids": allowed_document_ids,
            "can_answer": True,
            "route_status": route["route_status"],
            "reason": route["reason"],
        },
        "safety": safety,
        "safety_result": safety,
        "confidence": confidence,
        "retrieval": {
            "confidence": confidence["status"],
            "top_score": confidence["top_similarity"],
            "chunks": chunks,
        },
        "chunks": chunks,
        "answer": answer,
        "substitutions": substitutions,
        "citation_validation": citation_check,
        "unsupported_claims": unsupported_claims,
    }

