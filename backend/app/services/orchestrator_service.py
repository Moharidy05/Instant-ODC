from __future__ import annotations

from backend.app.schemas.ask import AskResponse, RetrievalPayload
from backend.app.schemas.evidence import EvidenceChunk
from backend.app.services.answer_service import run_full_pipeline
from src.safety.unsupported_claims import find_unsupported_claims


def _chunk_models(chunks: list[dict]) -> list[EvidenceChunk]:
    return [
        EvidenceChunk(
            chunk_id=str(chunk.get("chunk_id", "")),
            document_title=chunk.get("document_title"),
            section_title=chunk.get("section_title"),
            page_start=chunk.get("page_start"),
            page_end=chunk.get("page_end"),
            citation_label=chunk.get("citation_label"),
            chunk_type=chunk.get("chunk_type"),
            disease_layer=chunk.get("disease_layer"),
            similarity=float(chunk.get("similarity", 0.0) or 0.0),
            content=chunk.get("content", ""),
        )
        for chunk in chunks
    ]


def ask(
    *,
    question: str,
    disease_layer: str = "diabetes",
    language: str = "en",
    top_k: int = 5,
    show_chunks: bool = True,
) -> AskResponse:
    del language
    pipeline = run_full_pipeline(question=question, disease_layer=disease_layer, top_k=top_k)
    chunks = pipeline.get("chunks", [])
    confidence = pipeline.get("confidence", {})
    answer = pipeline.get("answer", "")
    unsupported_claims = pipeline.get("unsupported_claims")
    if unsupported_claims is None:
        unsupported_claims = find_unsupported_claims(answer, chunks) if chunks and isinstance(answer, str) else []

    visible_chunks = _chunk_models(chunks) if show_chunks else []
    return AskResponse(
        question=question,
        layer=pipeline.get("layer", {}),
        safety=pipeline.get("safety_result", {}),
        confidence=confidence,
        retrieval=RetrievalPayload(
            confidence=confidence.get("status", "insufficient"),
            top_score=float(confidence.get("top_similarity", 0.0) or 0.0),
            chunks=visible_chunks,
        ),
        answer=answer,
        substitutions=pipeline.get("substitutions", []),
        citation_validation=pipeline.get("citation_validation", {}),
        unsupported_claims=unsupported_claims,
    )
