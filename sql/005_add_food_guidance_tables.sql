-- Migration 005: Food guidance tables

create table if not exists food_items (
    id text primary key default gen_random_uuid()::text,
    name text not null,
    normalized_name text not null,
    category text,
    disease_layer text not null default 'diabetes',
    evidence_chunk_id text references guideline_chunks(chunk_id),
    citation_label text,
    created_at timestamptz default now()
);

create table if not exists food_guidance_rules (
    id text primary key default gen_random_uuid()::text,
    food_item_id text references food_items(id),
    classification text not null check (classification in (
        'encouraged',
        'suitable_with_caution',
        'better_to_limit',
        'not_supported_by_retrieved_evidence',
        'refused'
    )),
    rule_text text not null,
    disease_layer text not null default 'diabetes',
    evidence_chunk_id text references guideline_chunks(chunk_id),
    citation_label text,
    created_at timestamptz default now()
);

create table if not exists food_substitutions (
    id text primary key default gen_random_uuid()::text,
    source_food_item_id text references food_items(id),
    substitute_food_item_id text references food_items(id),
    substitution_text text not null,
    disease_layer text not null default 'diabetes',
    evidence_chunk_id text references guideline_chunks(chunk_id),
    citation_label text,
    created_at timestamptz default now()
);

create index if not exists idx_food_items_layer on food_items(disease_layer);
create index if not exists idx_food_guidance_rules_layer on food_guidance_rules(disease_layer);
create index if not exists idx_food_substitutions_layer on food_substitutions(disease_layer);
