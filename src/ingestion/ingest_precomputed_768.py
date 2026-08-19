
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from src.core.config import CHUNKS_TABLE
from src.db.supabase_client import get_admin_client


DOCUMENT_MAP = {
    "dc26s005": {
        "document_id": "ada_standards_2026_section_5",
        "document_title": "ADA Standards of Care in Diabetes 2026 - Section 5",
        "source_file": "dc26s005.pdf",
        "clinical_topic": "diabetes_food_safety",
        "disease_layer": "diabetes",
    },
    "KDIGO-2022-Clinical-Practice-Guideline-for-Diabetes-Management-in-CKD": {
        "document_id": "kdigo_2022_diabetes_ckd",
        "document_title": "KDIGO 2022 Clinical Practice Guideline for Diabetes Management in CKD",
        "source_file": "KDIGO-2022-Clinical-Practice-Guideline-for-Diabetes-Management-in-CKD.pdf",
        "clinical_topic": "diabetes_ckd",
        "disease_layer": "diabetes_ckd",
    },
    "dc24s010": {
        "document_id": "ada_2024_section_10_cvd",
        "document_title": "ADA Standards of Care 2024 - Cardiovascular Disease and Risk Management",
        "source_file": "dc24s010.pdf",
        "clinical_topic": "diabetes_cvd",
        "disease_layer": "diabetes_cvd",
    },
    "IWGDF-2023-01-Practical-Guidelines": {
        "document_id": "iwgdf_2023_practical_diabetes_foot",
        "document_title": "IWGDF 2023 Practical Guidelines on Diabetes-related Foot Disease",
        "source_file": "IWGDF-2023-01-Practical-Guidelines.pdf",
        "clinical_topic": "diabetes_foot",
        "disease_layer": "diabetes_foot",
    },
    "IWGDF-2023-02-Prevention-Guideline": {
        "document_id": "iwgdf_2023_prevention_diabetes_foot",
        "document_title": "IWGDF 2023 Prevention Guideline",
        "source_file": "IWGDF-2023-02-Prevention-Guideline.pdf",
        "clinical_topic": "diabetes_foot",
        "disease_layer": "diabetes_foot",
    },
    "IWGDF-2023-03-Classification-Guideline": {
        "document_id": "iwgdf_2023_classification_diabetes_foot",
        "document_title": "IWGDF 2023 Classification Guideline",
        "source_file": "IWGDF-2023-03-Classification-Guideline.pdf",
        "clinical_topic": "diabetes_foot",
        "disease_layer": "diabetes_foot",
    },
    "PIIS0168827824003295": {
        "document_id": "masld_metabolic_disease_guideline",
        "document_title": "MASLD / Metabolic Disease Clinical Practice Guideline",
        "source_file": "PIIS0168827824003295.pdf",
        "clinical_topic": "diabetes_masld",
        "disease_layer": "diabetes_masld",
    },
    "dci260082": {
        "document_id": "additional_diabetes_guideline_dci260082",
        "document_title": "Additional Diabetes Guideline Document",
        "source_file": "dci260082.pdf",
        "clinical_topic": "diabetes_misc",
        "disease_layer": "inactive_misc",
    },
}


def slugify(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_").lower() or "unknown_document"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def page_number_from_name(path: Path) -> int:
    match = re.search(r"page_(\d+)", path.stem)
    if match:
        return int(match.group(1))
    return 0


def metadata_for_doc(doc_name: str) -> dict[str, str]:
    if doc_name in DOCUMENT_MAP:
        return DOCUMENT_MAP[doc_name]

    safe = slugify(doc_name)
    return {
        "document_id": safe,
        "document_title": doc_name,
        "source_file": f"{doc_name}.pdf",
        "clinical_topic": "diabetes_misc",
        "disease_layer": "inactive_misc",
    }


def extract_text_from_anything(value: Any) -> list[str]:
    parts: list[str] = []

    if value is None:
        return parts

    if isinstance(value, str):
        text = value.strip()
        if text:
            parts.append(text)
        return parts

    if isinstance(value, list):
        for item in value:
            parts.extend(extract_text_from_anything(item))
        return parts

    if isinstance(value, dict):
        preferred_keys = [
            "title",
            "heading",
            "section",
            "section_title",
            "text",
            "content",
            "markdown",
            "caption",
            "summary",
        ]

        for key in preferred_keys:
            if key in value:
                parts.extend(extract_text_from_anything(value.get(key)))

        for key, item in value.items():
            if key in preferred_keys:
                continue
            if key.lower() in {"embedding", "vector", "bbox", "coordinates"}:
                continue
            parts.extend(extract_text_from_anything(item))

        return parts

    return parts


def build_page_text(extraction: dict[str, Any]) -> str:
    parts: list[str] = []

    for key in [
        "title",
        "section_title",
        "text",
        "content",
        "markdown",
        "sections",
        "blocks",
        "tables",
        "figures",
    ]:
        if key in extraction:
            parts.extend(extract_text_from_anything(extraction.get(key)))

    if not parts:
        parts.extend(extract_text_from_anything(extraction))

    cleaned: list[str] = []
    seen: set[str] = set()

    for part in parts:
        part = re.sub(r"\s+", " ", str(part)).strip()
        if not part:
            continue
        if part in seen:
            continue
        seen.add(part)
        cleaned.append(part)

    return "\n".join(cleaned).strip()


def infer_section_title(extraction: dict[str, Any], page_number: int) -> str:
    for key in ["section_title", "title", "heading"]:
        value = extraction.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:180]

    sections = extraction.get("sections")
    if isinstance(sections, list) and sections:
        first = str(sections[0]).strip()
        if first:
            return first[:180]

    return f"Page {page_number}"


def infer_chunk_type(text: str) -> str:
    t = text.lower()

    if any(word in t for word in ["recommend", "recommended", "should", "advised", "encouraged"]):
        return "recommendation"

    if any(word in t for word in ["risk", "warning", "avoid", "contraindicated", "hypoglycemia", "ketoacidosis"]):
        return "safety_warning"

    if any(word in t for word in ["table", "figure"]):
        return "table_or_figure"

    return "evidence"


def normalize_row(doc_name: str, extraction_path: Path, embedding_path: Path) -> tuple[dict[str, Any], dict[str, Any]] | None:
    extraction = load_json(extraction_path)
    embedding_obj = load_json(embedding_path)

    page_number = int(
        extraction.get("page_number")
        or extraction.get("page")
        or embedding_obj.get("page_number")
        or embedding_obj.get("page")
        or page_number_from_name(embedding_path)
    )

    embedding = embedding_obj.get("embedding")
    if not isinstance(embedding, list):
        return None

    if len(embedding) != 768:
        return None

    content = build_page_text(extraction)
    if len(content.strip()) < 30:
        return None

    meta = metadata_for_doc(doc_name)
    section_title = infer_section_title(extraction, page_number)

    chunk_id = f"{meta['document_id']}_p{page_number:04d}"

    document_row = {
        "id": meta["document_id"],
        "title": meta["document_title"],
        "source_file": meta["source_file"],
        "clinical_topic": meta["clinical_topic"],
        "credibility_note": "Imported from precomputed processed guideline extraction.",
        "public_use_note": "For educational RAG demo use only.",
        "license_warning": "Check source guideline license/public-use terms before redistribution.",
    }

    chunk_row = {
        "chunk_id": chunk_id,
        "document_id": meta["document_id"],
        "document_title": meta["document_title"],
        "source_file": meta["source_file"],
        "clinical_topic": meta["clinical_topic"],
        "disease_layer": meta["disease_layer"],
        "future_comorbidity_layer": None,
        "section_title": section_title,
        "page_start": page_number,
        "page_end": page_number,
        "chunk_type": infer_chunk_type(content),
        "content": content,
        "citation_label": f"{meta['document_title']}, page {page_number}",
        "embedding": [float(x) for x in embedding],
        "metadata": {
            "source": "precomputed_embedding_import",
            "original_document_folder": doc_name,
            "extraction_file": str(extraction_path).replace("\\", "/"),
            "embedding_file": str(embedding_path).replace("\\", "/"),
            "embedding_model": embedding_obj.get("model", "embeddinggemma"),
            "embedding_dimension": embedding_obj.get("dimension", 768),
            "truncated": embedding_obj.get("truncated", False),
        },
    }

    return document_row, chunk_row


def upsert_in_batches(client, table_name: str, rows: list[dict[str, Any]], batch_size: int, on_conflict: str) -> None:
    if not rows:
        return

    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        print(f"Upserting {table_name}: {start + 1} - {start + len(batch)} / {len(rows)}")

        client.table(table_name).upsert(
            batch,
            on_conflict=on_conflict,
        ).execute()


def ingest_precomputed_768(
    input_dir: Path,
    dry_run: bool,
    limit: int | None,
    batch_size: int,
    only_doc: str | None,
) -> None:
    extraction_root = input_dir / "extractions"
    embedding_root = input_dir / "embeddings"

    if not extraction_root.exists():
        raise FileNotFoundError(f"Missing extractions folder: {extraction_root}")

    if not embedding_root.exists():
        raise FileNotFoundError(f"Missing embeddings folder: {embedding_root}")

    documents_by_id: dict[str, dict[str, Any]] = {}
    chunks: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    doc_dirs = sorted([p for p in embedding_root.iterdir() if p.is_dir()])

    if only_doc:
        doc_dirs = [p for p in doc_dirs if p.name == only_doc]

    for doc_dir in doc_dirs:
        doc_name = doc_dir.name
        embedding_files = sorted(doc_dir.glob("page_*.json"))

        print(f"Scanning document: {doc_name} ({len(embedding_files)} embedding files)")

        for embedding_path in embedding_files:
            extraction_path = extraction_root / doc_name / embedding_path.name

            if not extraction_path.exists():
                failures.append({
                    "document": doc_name,
                    "file": embedding_path.name,
                    "reason": "missing_extraction_file",
                })
                continue

            try:
                normalized = normalize_row(doc_name, extraction_path, embedding_path)

                if normalized is None:
                    failures.append({
                        "document": doc_name,
                        "file": embedding_path.name,
                        "reason": "invalid_content_or_embedding",
                    })
                    continue

                document_row, chunk_row = normalized

                documents_by_id[document_row["id"]] = document_row
                chunks.append(chunk_row)

            except Exception as exc:
                failures.append({
                    "document": doc_name,
                    "file": embedding_path.name,
                    "reason": str(exc),
                })

            if limit and len(chunks) >= limit:
                break

        if limit and len(chunks) >= limit:
            break

    failure_path = Path("data/evaluation/precomputed_768_ingest_failures.jsonl")
    failure_path.parent.mkdir(parents=True, exist_ok=True)

    with failure_path.open("w", encoding="utf-8") as f:
        for item in failures:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    documents = list(documents_by_id.values())

    print("\n========== INGEST SUMMARY ==========")
    print("Input:", input_dir)
    print("Documents:", len(documents))
    print("Valid chunks:", len(chunks))
    print("Failures:", len(failures))
    print("Failures file:", failure_path)
    print("Target documents table: documents")
    print("Target chunks table:", CHUNKS_TABLE)
    print("Embedding dimension: 768")

    by_doc: dict[str, int] = {}
    for chunk in chunks:
        doc_id = chunk["document_id"]
        by_doc[doc_id] = by_doc.get(doc_id, 0) + 1

    print("\nChunks by document:")
    for doc_id, count in sorted(by_doc.items(), key=lambda x: x[1], reverse=True):
        print(f"- {doc_id}: {count}")

    if chunks:
        sample = dict(chunks[0])
        sample["embedding"] = sample["embedding"][:5] + ["..."]
        print("\nSample chunk:")
        print(json.dumps(sample, indent=2, ensure_ascii=False)[:4000])

    if dry_run:
        print("\nDry-run only. No rows were inserted.")
        return

    client = get_admin_client()

    print("\nUpserting documents...")
    upsert_in_batches(
        client=client,
        table_name="documents",
        rows=documents,
        batch_size=batch_size,
        on_conflict="id",
    )

    print("\nUpserting guideline chunks...")
    upsert_in_batches(
        client=client,
        table_name=CHUNKS_TABLE,
        rows=chunks,
        batch_size=batch_size,
        on_conflict="chunk_id",
    )

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest precomputed 768-dimensional EmbeddingGemma vectors into Supabase."
    )
    parser.add_argument(
        "--input",
        default="data/processed",
        help="Path containing extractions/ and embeddings/ folders.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview rows without inserting into Supabase.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of valid chunks for testing.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Supabase upsert batch size.",
    )
    parser.add_argument(
        "--only-doc",
        default=None,
        help="Import only one document folder, e.g. dc26s005.",
    )

    args = parser.parse_args()

    ingest_precomputed_768(
        input_dir=Path(args.input),
        dry_run=args.dry_run,
        limit=args.limit,
        batch_size=args.batch_size,
        only_doc=args.only_doc,
    )


if __name__ == "__main__":
    main()