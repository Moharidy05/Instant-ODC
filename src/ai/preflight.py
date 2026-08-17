from __future__ import annotations

import sys
import time


def _classify_error_text(text: str) -> str:
    message = text.lower()
    if any(h in message for h in ("403", "permission_denied", "permission denied", "denied access", "invalid api key")):
        return "credential_permission_error"
    if any(h in message for h in ("429", "quota", "resource_exhausted", "rate")):
        return "transient_or_quota"
    if any(h in message for h in ("404", "not found", "invalid model", "unsupported model")):
        return "model_unavailable"
    return "unknown_error"


def main() -> None:
    from src.core.config import (
        EMBEDDING_DIM,
        EMBEDDING_PROVIDER,
        GEMINI_EMBEDDING_API_KEYS,
        GEMINI_EMBEDDING_MODELS,
        GEMINI_GENERATION_API_KEYS,
        GEMINI_GENERATION_MODELS,
    )

    print(f"Embedding provider: {EMBEDDING_PROVIDER}")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    errors = 0

    if EMBEDDING_PROVIDER != "gemini":
        print("Preflight is configured for non-Gemini embeddings. This script is optimized for Gemini pools.")

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        print(f"google-genai import FAILED: {exc}")
        sys.exit(1)

    embedding_model = GEMINI_EMBEDDING_MODELS[0] if GEMINI_EMBEDDING_MODELS else "gemini-embedding-001"
    generation_model = GEMINI_GENERATION_MODELS[0] if GEMINI_GENERATION_MODELS else "gemini-2.0-flash"

    print("\nEmbedding keys:")
    embedding_ok = 0
    if not GEMINI_EMBEDDING_API_KEYS:
        print("No embedding keys configured.")
        errors += 1
    for idx, key in enumerate(GEMINI_EMBEDDING_API_KEYS):
        try:
            client = genai.Client(api_key=key)
            start = time.perf_counter()
            response = client.models.embed_content(
                model=embedding_model,
                contents="preflight diabetes food safety test",
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=EMBEDDING_DIM),
            )
            vec = list(response.embeddings[0].values) if response.embeddings else []
            if len(vec) != EMBEDDING_DIM:
                print(f"embedding_key[{idx}]: FAILED dimension_mismatch got={len(vec)}")
                errors += 1
            else:
                embedding_ok += 1
                print(f"embedding_key[{idx}]: OK ({round((time.perf_counter()-start)*1000)} ms)")
        except Exception as exc:
            print(f"embedding_key[{idx}]: FAILED {_classify_error_text(str(exc))}")

    print("\nGeneration keys:")
    generation_ok = 0
    if not GEMINI_GENERATION_API_KEYS:
        print("No generation keys configured.")
        errors += 1
    for idx, key in enumerate(GEMINI_GENERATION_API_KEYS):
        try:
            client = genai.Client(api_key=key)
            start = time.perf_counter()
            response = client.models.generate_content(
                model=generation_model,
                contents="Say OK",
                config=types.GenerateContentConfig(
                    system_instruction="You are a test assistant. Respond only with OK.",
                    max_output_tokens=10,
                    temperature=0,
                ),
            )
            text = (response.text or "").strip()
            if not text:
                print(f"generation_key[{idx}]: FAILED empty_response")
                errors += 1
            else:
                generation_ok += 1
                print(f"generation_key[{idx}]: OK ({round((time.perf_counter()-start)*1000)} ms)")
        except Exception as exc:
            print(f"generation_key[{idx}]: FAILED {_classify_error_text(str(exc))}")

    print("\nSummary:")
    print(f"Embedding usable keys: {embedding_ok}")
    print(f"Generation usable keys: {generation_ok}")

    if embedding_ok == 0:
        errors += 1
    if generation_ok == 0:
        errors += 1

    if errors:
        print("Preflight completed with errors. Fix key pools before full indexing.")
        sys.exit(1)
    print("Preflight completed successfully.")


if __name__ == "__main__":
    main()
