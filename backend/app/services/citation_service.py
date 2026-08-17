from __future__ import annotations

from src.answering.citation_validator import validate_citations


def validate_answer_citations(answer: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {"valid": True, "failures": [], "cited_chunk_ids": []}
    return validate_citations(answer, chunks)


def citations_from_chunks(answer: str, chunks: list[dict]) -> list[dict]:
    validation = validate_answer_citations(answer, chunks)
    cited = set(validation.get("cited_chunk_ids") or [])
    selected = []
    for chunk in chunks:
        cid = str(chunk.get("chunk_id", ""))
        if not cited or cid.lower() in cited:
            selected.append(
                {
                    "document_name": chunk.get("document_title", ""),
                    "section_title": chunk.get("section_title", ""),
                    "page_number": chunk.get("page_start"),
                    "chunk_id": cid,
                    "citation_label": chunk.get("citation_label", ""),
                }
            )
    return selected[:5]
