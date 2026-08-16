-- Migration 003: Create RPC function for vector similarity search

-- Function to match query embeddings against stored chunks
create or replace function match_guideline_chunks(
    query_embedding vector(1536),
    match_count int default 5,
    filter_clinical_topic text default null,
    filter_disease_layer text default null
)
returns table (
    chunk_id text,
    content text,
    document_title text,
    section_title text,
    page_start int,
    page_end int,
    citation_label text,
    chunk_type text,
    disease_layer text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        gc.chunk_id,
        gc.content,
        gc.document_title,
        gc.section_title,
        gc.page_start,
        gc.page_end,
        gc.citation_label,
        gc.chunk_type,
        gc.disease_layer,
        1 - (gc.embedding <=> query_embedding) as similarity
    from guideline_chunks gc
    where
        (filter_clinical_topic is null or gc.clinical_topic = filter_clinical_topic)
        and (filter_disease_layer is null or gc.disease_layer = filter_disease_layer)
    order by gc.embedding <=> query_embedding
    limit match_count;
end;
$$;
