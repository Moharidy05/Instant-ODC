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

### Dev Reset (after changing embedding dimension)

For local development after changing embedding dimension:

```text
sql/000_reset_dev_tables.sql   (DEV ONLY — drops all tables)
sql/001_enable_pgvector.sql
sql/002_create_tables.sql
sql/003_match_chunks_function.sql
sql/004_add_retrieval_logs.sql
sql/005_add_food_guidance_tables.sql
```

Then re-index: `python3 -m src.ingestion.index_supabase`

## Preflight

```bash
python3 -m src.ai.preflight
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

## FastAPI Backend

The backend is separate from the Streamlit demo and lives under `backend/app`.
It is intentionally only an API layer: RAG orchestration, retrieval, Gemini fallback, disease layers, safety rules, answer generation, citation validation, food lists, and substitutions remain in `src/`.

Run locally:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

List disease layers:

```bash
curl http://localhost:8000/layers
```

Ask a grounded food-safety question:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Are legumes encouraged for diabetes?",
    "disease_layer": "diabetes",
    "language": "en",
    "top_k": 5,
    "show_chunks": true
  }'
```

Search evidence without generation:

```bash
curl -X POST http://localhost:8000/evidence/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sugar-sweetened beverages",
    "disease_layer": "diabetes",
    "top_k": 10
  }'
```

Get food guidance lists:

```bash
curl "http://localhost:8000/foods/guidance-list?disease_layer=diabetes"
```

Get evidence-tied substitutions:

```bash
curl -X POST http://localhost:8000/foods/substitutions \
  -H "Content-Type: application/json" \
  -d '{
    "food": "orange juice",
    "disease_layer": "diabetes",
    "language": "en"
  }'
```

Run backend evaluation:

```bash
curl -X POST http://localhost:8000/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "disease_layer": "diabetes"}'
```

Frontend demo:

```bash
cd frontend
cp .env.example .env
pnpm install
pnpm dev --host 0.0.0.0
```

If `pnpm` is unavailable:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open `http://localhost:5173`. The React app calls the FastAPI backend and shows an explicit offline fallback label if the backend is unreachable.

Streamlit backup demo:

```bash
streamlit run app.py --server.port 8501
```

Open `http://localhost:8501`.

Useful demo API examples:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/layers
curl "http://localhost:8000/foods/guidance-list?disease_layer=diabetes"

curl -X POST http://localhost:8000/evidence/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Can a person with diabetes drink orange juice?","disease_layer":"diabetes","clinical_topic":"diabetes_food_safety","top_k":5}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Can a person with diabetes drink orange juice?","disease_layer":"diabetes","language":"en","top_k":5,"show_chunks":true}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How much insulin should I take after eating rice?","disease_layer":"diabetes","language":"en","top_k":5,"show_chunks":true}'

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Who won the world cup?","disease_layer":"diabetes","language":"en","top_k":5,"show_chunks":true}'

curl -X POST http://localhost:8000/foods/substitutions \
  -H "Content-Type: application/json" \
  -d '{"food":"orange juice","disease_layer":"diabetes","language":"en"}'

curl -X POST http://localhost:8000/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{"limit":10,"disease_layer":"diabetes"}'
```

Duplicate diagnostics:

```text
sql/006_diagnostics.sql
sql/007_deduplicate_guideline_chunks.sql  (optional, manual only if duplicates exist)
```

Backend safety notes:

- `/health` reports readiness booleans only; it never returns secret values.
- API retrieval uses anon-key Supabase access when configured.
- Supabase service-role access remains restricted to ingestion/admin scripts.
- If Supabase or Gemini are not configured, local lexical retrieval and deterministic answer fallback keep the demo/test path usable.
- Local frontend CORS origins are configurable with `BACKEND_CORS_ORIGINS`.

Backend tests:

```bash
pytest tests/test_backend.py
```

## Validation

```bash
python3 -m py_compile $(find src -name "*.py")
python3 -m py_compile $(find backend -name "*.py")
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
