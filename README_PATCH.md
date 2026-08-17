# Gemini quota patch

Copy these files over the same paths in your project. This patch does not include `.env` and does not include API keys.

Run:

```bash
python3 -m py_compile src/core/config.py src/core/logging.py src/ai/fallback_router.py src/ai/embeddings.py src/ai/preflight.py src/ingestion/index_supabase.py
python3 -m src.ai.preflight
python3 -m src.ingestion.index_supabase --only-missing
```

Make sure Supabase SQL uses `vector(1536)` for Gemini embeddings.
