-- Migration 004: Retrieval logging

create table if not exists retrieval_logs (
    id bigint generated always as identity primary key,
    query text not null,
    disease_layer text not null,
    chunk_id text,
    rank int,
    similarity float,
    section text,
    page int,
    created_at timestamptz default now()
);

create index if not exists idx_retrieval_logs_layer on retrieval_logs(disease_layer);
create index if not exists idx_retrieval_logs_chunk_id on retrieval_logs(chunk_id);
create index if not exists idx_retrieval_logs_created_at on retrieval_logs(created_at);
