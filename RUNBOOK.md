# Runbook

## 1. Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with Supabase and Gemini credentials. Do not commit real `.env` values.

## 2. Required Environment Variables

Required for hosted retrieval/generation: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_EMBEDDING_API_KEY_0`, and `GEMINI_GENERATION_API_KEY_0`.

Defaults are documented in `.env.example`, including Gemini model pools, `EMBEDDING_DIM=1536`, retrieval top-k settings, disease layer defaults, and backend CORS origins.

## 3. SQL Migration Order

```text
sql/001_enable_pgvector.sql
sql/002_create_tables.sql
sql/003_match_chunks_function.sql
sql/004_add_retrieval_logs.sql
sql/005_add_food_guidance_tables.sql
sql/006_diagnostics.sql
```

Use `sql/000_reset_dev_tables.sql` only for local/dev resets. Use `sql/007_deduplicate_guideline_chunks.sql` only if `006_diagnostics.sql` shows duplicate `chunk_id` rows.

## 4. Indexing Commands

```bash
.venv/bin/python -m src.ingestion.extract_pdf
.venv/bin/python -m src.ingestion.inspect_pages
.venv/bin/python -m src.ingestion.chunk_sections
.venv/bin/python -m src.ingestion.index_supabase
```

Expected local artifacts: `data/extracted/extracted_pages.jsonl` and `data/chunks/chunks.jsonl`.

## 5. AI Service Tests

```bash
.venv/bin/python -m py_compile $(find src backend streamlit_demo -name "*.py") app.py
.venv/bin/python -m src.ai.preflight
.venv/bin/python -m src.retrieval.evaluation
.venv/bin/python -m src.evaluate
.venv/bin/python -m pytest tests/test_backend.py
```

Preflight should show `Embedding usable keys: >= 1` and `Generation usable keys: >= 1` when `.env` is configured.

## 6. Backend Run

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for OpenAPI.

## 7. Frontend Run

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

Open `http://localhost:5173`.

## 8. Streamlit Run

```bash
streamlit run app.py --server.port 8501
```

Open `http://localhost:8501`.

## 9. Demo Test Questions

- Are legumes encouraged for diabetes?
- Can a person with diabetes drink orange juice?
- Is water better than soda for diabetes?
- Are processed foods recommended for people with diabetes?
- How much insulin should I take after eating rice?
- I have diabetes and kidney disease. Can I eat bananas daily?
- Who won the world cup?

## 10. Troubleshooting

- `python3 -m pip` missing: create `.venv` first and use `.venv/bin/python -m pip`.
- Preflight key count is zero: check `.env` names exactly match `.env.example`.
- Backend health shows `local_lexical_fallback`: Supabase URL or anon key is missing.
- `/ask` returns insufficient evidence: inspect `/evidence/search` chunks and rerun indexing if Supabase is stale.
- Frontend says backend offline: start FastAPI on port 8000 and confirm `VITE_API_BASE_URL=http://localhost:8000`.
- Duplicate index rows: run `sql/006_diagnostics.sql`; only then consider `sql/007_deduplicate_guideline_chunks.sql`.
