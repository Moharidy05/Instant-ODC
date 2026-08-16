"""Supabase indexing module for the RAG pipeline.

This module reads processed document chunks from a JSONL file,
generates embeddings for their content, and upserts them into
the Supabase database.
"""
import json
import time
import statistics
from pathlib import Path

from src.supabase_client import get_admin_client
from src.embeddings import embed_batch

def main():
    """Main execution function for the indexing process.
    
    - Initializes the Supabase admin client.
    - Upserts the main document record.
    - Reads chunk data from JSONL.
    - Batches chunks and generates embeddings.
    - Upserts chunks to the Supabase database.
    - Outputs summary statistics.
    """
    print("Starting indexing process...")
    supabase = get_admin_client()
    
    # 1. Upsert document record
    document_data = {
        'id': 'ada_standards_2026_section_5',
        'title': 'ADA Standards of Care in Diabetes 2026 - Section 5',
        'source_file': 'dc26s005.pdf',
        'clinical_topic': 'diabetes_food_safety',
        'credibility_note': 'Official ADA clinical practice recommendation',
        'public_use_note': 'Suitable for educational, noncommercial use if properly cited',
        'license_warning': 'Text/data mining may require prior written permission from ADA'
    }
    
    print("Inserting document record...")
    try:
        supabase.table('documents').upsert(document_data, on_conflict='id').execute()
        print("Document record inserted successfully.")
    except Exception as e:
        print(f"Error inserting document record: {e}")
        return

    # 2. Read chunks
    chunks_path = Path('data/chunks/chunks.jsonl')
    if not chunks_path.exists():
        print(f"Error: {chunks_path} not found.")
        return

    chunks = []
    with open(chunks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    total_chunks = len(chunks)
    print(f"Loaded {total_chunks} chunks from {chunks_path}.")
    
    if total_chunks == 0:
        print("No chunks to process.")
        return

    # 3. Process and upsert chunks in batches
    batch_size = 50
    inserted_count = 0
    failed_count = 0
    content_lengths = []
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} chunks)...")
        
        texts_to_embed = [chunk['content'] for chunk in batch]
        
        try:
            # Generate embeddings for the batch
            embeddings = embed_batch(texts_to_embed)
        except Exception as e:
            print(f"Error generating embeddings for batch starting at index {i}: {e}")
            print("Waiting 10 seconds before continuing...")
            time.sleep(10)
            failed_count += len(batch)
            continue
            
        # Prepare data for upsert — map all chunk fields to DB columns
        upsert_data = []
        for j, chunk in enumerate(batch):
            content_lengths.append(len(chunk['content']))

            # Construct the record matching the guideline_chunks table schema
            record = {
                'id': chunk['chunk_id'],               # PK — use chunk_id as the row id
                'document_id': chunk.get('document_id', 'ada_standards_2026_section_5'),
                'chunk_id': chunk['chunk_id'],          # Also stored in dedicated column
                'document_title': chunk.get('document_title', ''),
                'source_file': chunk.get('source_file', 'dc26s005.pdf'),
                'clinical_topic': chunk.get('clinical_topic', 'diabetes_food_safety'),
                'disease_layer': chunk.get('disease_layer', 'diabetes'),
                'future_comorbidity_layer': chunk.get('future_comorbidity_layer'),
                'section_title': chunk.get('section_title', ''),
                'page_start': chunk.get('page_start'),
                'page_end': chunk.get('page_end'),
                'chunk_type': chunk.get('chunk_type', 'other'),
                'content': chunk['content'],
                'citation_label': chunk.get('citation_label', ''),
                'embedding': embeddings[j],
                'metadata': {
                    'clinical_topic': chunk.get('clinical_topic'),
                    'disease_layer': chunk.get('disease_layer'),
                    'chunk_type': chunk.get('chunk_type'),
                },
            }
            upsert_data.append(record)
            
        # Upsert to Supabase — idempotent via 'id' (which is the chunk_id)
        try:
            supabase.table('guideline_chunks').upsert(upsert_data, on_conflict='id').execute()
            inserted_count += len(upsert_data)
        except Exception as e:
            print(f"Error upserting chunks to Supabase: {e}")
            # Try individually if batch fails
            for record in upsert_data:
                try:
                    supabase.table('guideline_chunks').upsert(record, on_conflict='id').execute()
                    inserted_count += 1
                except Exception as ex:
                    print(f"Error upserting chunk {record['id']}: {ex}")
                    failed_count += 1
            
        # Sleep slightly to avoid overwhelming the API or DB
        time.sleep(0.5)
        
    # 4. Print summary
    avg_length = statistics.mean(content_lengths) if content_lengths else 0
    print("\n--- Indexing Summary ---")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Successfully inserted: {inserted_count}")
    print(f"Failed to insert: {failed_count}")
    print(f"Average content length: {avg_length:.2f} characters")

if __name__ == "__main__":
    main()
