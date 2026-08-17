-- Migration 002: Create necessary tables for the RAG system

-- Table to store high-level document metadata
create table documents (
    id text primary key,
    title text,
    source_file text,
    clinical_topic text,
    credibility_note text,
    public_use_note text,
    license_warning text,
    created_at timestamptz default now()
);

-- Table to store individual text chunks and their embeddings
create table guideline_chunks (
    id text primary key default gen_random_uuid()::text,
    document_id text references documents(id),
    chunk_id text unique not null,
    document_title text,
    source_file text,
    clinical_topic text,
    disease_layer text,
    future_comorbidity_layer text null,
    section_title text,
    page_start int,
    page_end int,
    chunk_type text,
    content text not null,
    citation_label text,
    embedding vector(1536),
    metadata jsonb,
    created_at timestamptz default now()
);

-- Create indexes for faster filtering and similarity search
create index idx_guideline_chunks_clinical_topic on guideline_chunks(clinical_topic);
create index idx_guideline_chunks_disease_layer on guideline_chunks(disease_layer);
create index idx_guideline_chunks_document_id on guideline_chunks(document_id);

-- Create an IVFFlat index on the embedding column using cosine distance.
-- lists=10 is used since we expect < 1000 chunks.
create index idx_guideline_chunks_embedding on guideline_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 10);
