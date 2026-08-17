from __future__ import annotations

import re


def validate_citations(answer: str, chunks: list[dict]) -> dict:
    failures: list[str] = []
    answer_lower = (answer or "").lower()
    cited_chunk_ids = set(re.findall(r"\b[a-z0-9_]+_p\d+_c\d+\b", answer_lower))
    chunk_ids = {str(c.get("chunk_id", "")).lower() for c in chunks}

    if not cited_chunk_ids:
        failures.append("No chunk IDs found in answer.")
    for cid in cited_chunk_ids:
        if cid not in chunk_ids:
            failures.append(f"Cited chunk ID not retrieved: {cid}")

    for chunk in chunks:
        cid = str(chunk.get("chunk_id", "")).lower()
        if cid and cid in cited_chunk_ids:
            doc = str(chunk.get("document_title", "")).lower()
            section = str(chunk.get("section_title", "")).lower()
            page = str(chunk.get("page_start", ""))
            if doc and doc not in answer_lower:
                failures.append(f"Document title missing for cited chunk {cid}.")
            if section and section not in answer_lower:
                failures.append(f"Section title missing for cited chunk {cid}.")
            if page and page not in answer_lower:
                failures.append(f"Page missing for cited chunk {cid}.")

    return {
        "valid": not failures,
        "failures": failures,
        "cited_chunk_ids": sorted(cited_chunk_ids),
    }
