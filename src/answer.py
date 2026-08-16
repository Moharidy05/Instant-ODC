"""
Answer generation module for the Diabetes Food Safety RAG pipeline.
===================================================================

Uses Google Gemini (GenAI SDK) to generate grounded answers from
retrieved guideline evidence chunks.  The LLM is instructed to answer
ONLY from the provided evidence and to refuse outside knowledge.

Functions:
    generate_answer  — Single answer from chunks + safety result
    full_pipeline    — End-to-end: safety → retrieval → answer
"""

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_GENERATION_MODEL
from src.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    REFUSE_TEMPLATE,
    CAUTION_TEMPLATE,
    SAFETY_NOTE,
)
from src.safety import classify_query
from src.retrieve import retrieve_chunks

# ──────────────────────────────────────────────────────────────
# Initialise the Gemini client once at module load
# ──────────────────────────────────────────────────────────────
_client = genai.Client(api_key=GEMINI_API_KEY)


def generate_answer(query: str, chunks: list[dict], safety_result: dict) -> str:
    """Generate an evidence-grounded answer using Gemini.

    Args:
        query:          The user's original question.
        chunks:         Retrieved guideline evidence chunks.
        safety_result:  Output of ``classify_query`` (safety_label, reason, …).

    Returns:
        A formatted answer string, or a refusal/caution message.
    """
    # ── Refuse outright if the safety layer says so ──────────
    if safety_result["safety_label"] == "refuse":
        return REFUSE_TEMPLATE.format(
            reason=safety_result["reason"],
            safety_note=SAFETY_NOTE,
        )

    # ── Format evidence chunks into a context block ─────────
    context_parts: list[str] = []
    for idx, chunk in enumerate(chunks, 1):
        doc = chunk.get("document_title", "Unknown Doc")
        sec = chunk.get("section_title", "Unknown Sec")
        pg = chunk.get("page_start", "N/A")
        cite = chunk.get("citation_label", "")
        content = chunk.get("content", "")
        context_parts.append(
            f"Chunk {idx} (Doc: {doc}, Sec: {sec}, Page: {pg}):\n"
            f"{content}\n"
            f"[Citation: {cite}]"
        )
    evidence_text = "\n\n".join(context_parts)

    # ── Build the user prompt ───────────────────────────────
    user_prompt = USER_PROMPT_TEMPLATE.format(
        query=query,
        evidence_chunks=evidence_text,
    )

    # Prepend caution framing if needed
    if safety_result["safety_label"] == "needs_caution":
        user_prompt = (
            CAUTION_TEMPLATE.format(reason=safety_result["reason"])
            + "\n\n"
            + user_prompt
        )

    # ── Call Gemini for generation ──────────────────────────
    response = _client.models.generate_content(
        model=GEMINI_GENERATION_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,          # Low temperature for factual answers
            max_output_tokens=2048,
        ),
    )

    return response.text


def full_pipeline(
    query: str,
    clinical_topic: str = "diabetes_food_safety",
    disease_layer: str = "diabetes",
    top_k: int = 5,
) -> dict:
    """Execute the full RAG pipeline: Safety → Retrieval → Answer.

    Returns a dict with keys: query, safety_result, chunks, answer.
    """
    # Step 1: Safety classification
    safety_result = classify_query(query)

    # Step 2: Retrieve evidence chunks (skip if refused)
    chunks = []
    if safety_result["safety_label"] != "refuse":
        chunks = retrieve_chunks(query, clinical_topic, disease_layer, top_k)

    # Step 3: Generate grounded answer
    answer = generate_answer(query, chunks, safety_result)

    return {
        "query": query,
        "safety_result": safety_result,
        "chunks": chunks,
        "answer": answer,
    }
