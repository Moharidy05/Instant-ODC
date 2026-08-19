from __future__ import annotations

import re

from src.retrieval.scoring import keyword_overlap_score


SECTION_LABEL_RE = re.compile(r"^(Food Safety Classification|Short Answer|Why|Better Alternative|Evidence Excerpt|Citations|Safety Note):", re.I)
SAFETY_DISCLAIMER_PHRASES = (
    "not a personalized diet plan",
    "medical prescription",
    "consult a qualified clinician",
    "registered dietitian",
    "safety note",
    "individualized nutrition therapy",
    "personalized medical advice",
)


def split_sentences(text: str) -> list[str]:
    cleaned = "\n".join(line.strip() for line in (text or "").splitlines() if line.strip())
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p.strip() for p in parts if p.strip()]


def find_unsupported_claims(answer: str, chunks: list[dict], min_overlap: float = 0.18) -> list[dict]:
    evidence = " ".join(chunk.get("content", "") for chunk in chunks)
    unsupported: list[dict] = []
    for sentence in split_sentences(answer):
        if SECTION_LABEL_RE.match(sentence) or len(sentence) < 25:
            continue
        sentence_lower = sentence.lower()
        if any(phrase in sentence_lower for phrase in SAFETY_DISCLAIMER_PHRASES):
            continue
        overlap = keyword_overlap_score(sentence, evidence)
        if overlap < min_overlap:
            unsupported.append({"sentence": sentence, "overlap": round(overlap, 3)})
    return unsupported
