# Diabetes Food Safety Navigator

Evidence-based clinical RAG for adult diabetes food safety and nutrition questions.

The system answers questions such as:

- “Can I eat this as a person with diabetes?”
- “Is this food suitable for diabetes?”
- “What can I eat instead?”
- “Show me foods that are encouraged / caution / better to limit.”

This is not a personalized diet planner, prescription system, insulin dosing tool, medication adjustment tool, emergency care tool, or comorbidity-specific advisor unless the matching official disease layer has been indexed and activated.

## Source

- ADA Standards of Care in Diabetes 2026, Section 5
- Local source file: `data/raw/dc26s005.pdf`
- Indexed layer: `diabetes`
- Future inactive layers: CKD, CVD, pregnancy, hypertension

## Setup

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with Supabase and Gemini credentials. Do not commit real API keys.

## SQL

Run the migrations in Supabase in order:

```text
sql/001_enable_pgvector.sql
sql/002_create_tables.sql
sql/003_match_chunks_function.sql
sql/004_add_retrieval_logs.sql
sql/005_add_food_guidance_tables.sql
```

## Pipeline

```bash
python3 -m src.ingestion.extract_pdf
python3 -m src.ingestion.inspect_pages
python3 -m src.ingestion.chunk_sections
python3 -m src.ingestion.index_supabase
python3 -m src.retrieval.evaluation
python3 -m src.evaluate
```

Run the demo:

```bash
streamlit run app.py
```

## Validation

```bash
python3 -m py_compile $(find src -name "*.py")
python3 -c "from src.retrieval.retrieve import retrieve_chunks; from src.answering.answer import generate_answer; print('imports ok')"
```

## Current architecture

```text
config/              disease layers, retrieval, safety, fallback config
src/core/            config, logging, errors
src/ai/              Gemini fallback routing, embeddings, generation
src/ingestion/       PDF extraction, inspection, chunking, Supabase indexing
src/db/              Supabase client
src/layers/          disease-layer orchestration
src/retrieval/       retrieval, reranking, scoring, Day 2 evaluation
src/safety/          guardrails, confidence threshold, unsupported claim checks
src/answering/       prompts, grounded answering, citation validation
src/food/            food classification, substitutions, list generation
src/api/             request/response schemas
streamlit_demo/      tabbed UI
sql/                 migrations
data/evaluation/     test set and generated evaluation reports
```

If Supabase/Gemini are not configured, local evaluation falls back to lexical retrieval over `data/chunks/chunks.jsonl`. Production retrieval uses Supabase pgvector and Gemini embeddings/generation.
