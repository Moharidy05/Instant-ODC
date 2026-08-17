from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from src.ai.embeddings import embed_batch
from src.core.config import DOCUMENT_ID, DOCUMENT_TITLE, PROJECT_TOPIC, SOURCE_FILE, project_path
from src.db.supabase_client import get_admin_client, supabase_configured


def main() -> None:
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
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    total_chunks = len(chunks)
    print(f"Loaded {total_chunks} chunks from {chunks_path}.")
    inserted_count = failed_count = 0
    content_lengths: list[int] = []
    batch_size = 50
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch)} chunks)...")
        try:
            embeddings = embed_batch([chunk["content"] for chunk in batch])
        except Exception as exc:
            print(f"Error generating embeddings for batch starting at index {i}: {exc}")
            failed_count += len(batch)
            time.sleep(2)
            continue
        upsert_data = []
        for j, chunk in enumerate(batch):
            content_lengths.append(len(chunk["content"]))
            upsert_data.append(
                {
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
                    "embedding": embeddings[j],
                    "metadata": {
                        "clinical_topic": chunk.get("clinical_topic"),
                        "disease_layer": chunk.get("disease_layer"),
                        "chunk_type": chunk.get("chunk_type"),
                    },
                }
            )
        try:
            supabase.table("guideline_chunks").upsert(upsert_data, on_conflict="id").execute()
            inserted_count += len(upsert_data)
        except Exception as exc:
            print(f"Batch upsert failed: {exc}")
            for record in upsert_data:
                try:
                    supabase.table("guideline_chunks").upsert(record, on_conflict="id").execute()
                    inserted_count += 1
                except Exception as item_exc:
                    print(f"Error upserting chunk {record['id']}: {item_exc}")
                    failed_count += 1
        time.sleep(0.5)
    avg_length = statistics.mean(content_lengths) if content_lengths else 0
    print("\n--- Indexing Summary ---")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Successfully inserted: {inserted_count}")
    print(f"Failed to insert: {failed_count}")
    print(f"Average content length: {avg_length:.2f} characters")


if __name__ == "__main__":
    main()
