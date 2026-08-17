from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from src.ai.embeddings import embed_batch, embed_text
from src.core.config import (
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_PROVIDER,
    EMBEDDING_SLEEP_SECONDS,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    PROJECT_TOPIC,
    SOURCE_FILE,
    project_path,
)
from src.db.supabase_client import get_admin_client, supabase_configured

FAILED_PATH = project_path("data", "evaluation", "indexing_failed_chunks.jsonl")
PROGRESS_PATH = project_path("data", "evaluation", "indexing_progress.json")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_progress(data: dict[str, Any]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_existing_chunk_ids(supabase: object) -> set[str]:
    """Fetch chunk IDs already present in the database."""
    try:
        # 464 chunks only, so one page is enough for this project.
        response = supabase.table("guideline_chunks").select("chunk_id").limit(5000).execute()  # type: ignore[union-attr]
        return {row["chunk_id"] for row in (response.data or []) if row.get("chunk_id")}
    except Exception as exc:
        print(f"Warning: Could not fetch existing chunk IDs: {exc}")
        return set()


def _active_embedding_info() -> tuple[str, str]:
    if EMBEDDING_PROVIDER == "local":
        return "local", LOCAL_EMBEDDING_MODEL
    return "gemini", GEMINI_EMBEDDING_MODEL


def _load_failed_chunk_ids() -> set[str]:
    if not FAILED_PATH.exists():
        return set()
    ids: set[str] = set()
    for line in FAILED_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if row.get("chunk_id"):
                ids.add(row["chunk_id"])
        except Exception:
            continue
    return ids


def _make_record(chunk: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
    return {
        "id": chunk["chunk_id"],
        "document_id": chunk.get("document_id", DOCUMENT_ID),
        "chunk_id": chunk["chunk_id"],
        "document_title": chunk.get("document_title", DOCUMENT_TITLE),
        "source_file": chunk.get("source_file", SOURCE_FILE),
        "clinical_topic": chunk.get("clinical_topic", PROJECT_TOPIC),
        "disease_layer": chunk.get("disease_layer", "diabetes"),
        "future_comorbidity_layer": chunk.get("future_comorbidity_layer"),
        "section_title": chunk.get("section_title", ""),
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "chunk_type": chunk.get("chunk_type", "other"),
        "content": chunk["content"],
        "citation_label": chunk.get("citation_label", ""),
        "embedding": embedding,
        "metadata": {
            "clinical_topic": chunk.get("clinical_topic"),
            "disease_layer": chunk.get("disease_layer"),
            "chunk_type": chunk.get("chunk_type"),
        },
    }


def _upsert_records(supabase: object, records: list[dict[str, Any]]) -> tuple[int, list[str]]:
    """Return (inserted_count, failed_chunk_ids)."""
    try:
        supabase.table("guideline_chunks").upsert(records, on_conflict="id").execute()
        return len(records), []
    except Exception as exc:
        print(f"Batch upsert failed, trying one-by-one: {exc}")

    inserted = 0
    failed: list[str] = []
    for record in records:
        try:
            supabase.table("guideline_chunks").upsert(record, on_conflict="id").execute()
            inserted += 1
        except Exception as item_exc:
            chunk_id = record.get("chunk_id") or record.get("id")
            print(f"Error upserting chunk {chunk_id}: {item_exc}")
            failed.append(str(chunk_id))
    return inserted, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Index chunks into Supabase.")
    parser.add_argument("--only-missing", action="store_true", help="Skip chunks already in the DB. This is default now.")
    parser.add_argument("--limit", type=int, default=0, help="Max chunks to process (0 = all).")
    parser.add_argument("--retry-failed", action="store_true", help="Process only chunk IDs previously logged as failed.")
    args = parser.parse_args()

    provider, model_name = _active_embedding_info()
    print(f"Embedding provider: {provider}")
    print(f"Embedding model: {model_name}")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    print(f"Embedding batch size: {EMBEDDING_BATCH_SIZE}")
    print(f"Sleep between batches: {EMBEDDING_SLEEP_SECONDS}s")
    print()

    print("Starting indexing process...")
    if not supabase_configured(admin=True):
        print("Supabase service credentials are not configured. Skipping remote indexing.")
        return

    supabase = get_admin_client()

    document_data = {
        "id": DOCUMENT_ID,
        "title": DOCUMENT_TITLE,
        "source_file": SOURCE_FILE,
        "clinical_topic": PROJECT_TOPIC,
        "credibility_note": "Official ADA clinical practice recommendation",
        "public_use_note": "Suitable for educational, noncommercial use if properly cited",
        "license_warning": "Text/data mining may require prior written permission from ADA",
    }
    supabase.table("documents").upsert(document_data, on_conflict="id").execute()

    chunks_path = project_path("data", "chunks", "chunks.jsonl")
    if not chunks_path.exists():
        print(f"Error: {chunks_path} not found.")
        return

    all_chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(all_chunks)} total chunks from {chunks_path}.")

    existing_ids = _get_existing_chunk_ids(supabase)
    print(f"Already indexed: {len(existing_ids)}")

    chunks = [c for c in all_chunks if c["chunk_id"] not in existing_ids]
    print(f"Missing chunks to index: {len(chunks)}")

    if args.retry_failed:
        failed_ids = _load_failed_chunk_ids()
        chunks = [c for c in all_chunks if c["chunk_id"] in failed_ids and c["chunk_id"] not in existing_ids]
        print(f"Retry-failed mode: {len(chunks)} chunks after filtering failed IDs and skipping existing.")

    if args.limit > 0:
        chunks = chunks[: args.limit]
        print(f"Limit applied: {len(chunks)} chunks")

    total_chunks = len(chunks)
    if total_chunks == 0:
        print("Nothing to index.")
        _write_progress({"total_source_chunks": len(all_chunks), "already_indexed": len(existing_ids), "missing": 0})
        return

    inserted_count = failed_count = 0
    content_lengths: list[int] = []
    failed_rows: list[dict[str, Any]] = []
    batch_size = max(1, EMBEDDING_BATCH_SIZE)

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch)} chunks)...")
        embeddings: list[list[float]] = []

        try:
            embeddings = embed_batch([chunk["content"] for chunk in batch], kind="document", batch_size=batch_size)
        except Exception as batch_exc:
            print(f"Batch embedding failed at index {i}: {batch_exc}")
            print("Trying one-by-one embedding for this batch...")
            for chunk in batch:
                try:
                    embeddings.append(embed_text(chunk["content"], kind="document"))
                except Exception as item_exc:
                    failed_count += 1
                    failed_rows.append({"chunk_id": chunk["chunk_id"], "reason": str(item_exc)[:500]})
                    print(f"Embedding failed for chunk {chunk['chunk_id']}: {item_exc}")
                    embeddings.append([])

        if len(embeddings) != len(batch):
            reason = f"Embedding count mismatch: expected {len(batch)}, got {len(embeddings)}"
            print(reason)
            for chunk in batch:
                failed_count += 1
                failed_rows.append({"chunk_id": chunk["chunk_id"], "reason": reason})
            time.sleep(EMBEDDING_SLEEP_SECONDS)
            continue

        records: list[dict[str, Any]] = []
        for chunk, emb in zip(batch, embeddings):
            if len(emb) != EMBEDDING_DIM:
                reason = f"Dimension mismatch: expected {EMBEDDING_DIM}, got {len(emb)}"
                print(f"Skipping chunk {chunk['chunk_id']}: {reason}")
                failed_count += 1
                failed_rows.append({"chunk_id": chunk["chunk_id"], "reason": reason})
                continue
            content_lengths.append(len(chunk["content"]))
            records.append(_make_record(chunk, emb))

        if records:
            inserted, upsert_failed_ids = _upsert_records(supabase, records)
            inserted_count += inserted
            failed_count += len(upsert_failed_ids)
            for chunk_id in upsert_failed_ids:
                failed_rows.append({"chunk_id": chunk_id, "reason": "upsert failed"})

        _write_progress(
            {
                "total_source_chunks": len(all_chunks),
                "already_indexed_at_start": len(existing_ids),
                "target_missing_this_run": total_chunks,
                "processed_this_run": min(i + len(batch), total_chunks),
                "inserted_this_run": inserted_count,
                "failed_this_run": failed_count,
                "embedding_provider": EMBEDDING_PROVIDER,
                "embedding_dim": EMBEDDING_DIM,
            }
        )
        time.sleep(EMBEDDING_SLEEP_SECONDS)

    if failed_rows:
        _write_jsonl(FAILED_PATH, failed_rows)

    avg_length = statistics.mean(content_lengths) if content_lengths else 0
    print("\n--- Indexing Summary ---")
    print(f"Total chunks attempted this run: {total_chunks}")
    print(f"Successfully inserted this run: {inserted_count}")
    print(f"Failed this run: {failed_count}")
    print(f"Average content length: {avg_length:.2f} characters")
    if failed_rows:
        print(f"Failed chunks logged to: {FAILED_PATH}")
        print(f"First failed chunk IDs: {[r['chunk_id'] for r in failed_rows[:20]]}")


if __name__ == "__main__":
    main()
