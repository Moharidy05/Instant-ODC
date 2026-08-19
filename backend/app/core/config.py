from __future__ import annotations

import importlib.util
import os
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field

from src.core import config as src_config
from src.layers.disease_layer_orchestrator import layer_status_rows


class BackendSettings(BaseModel):
    app_name: str = "Diabetes Food Safety Navigator API"
    app_version: str = "0.2.0"
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "BACKEND_CORS_ORIGINS",
                "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501",
            ).split(",")
            if origin.strip()
        ]
    )
    project_topic: str = src_config.PROJECT_TOPIC
    default_disease_layer: str = src_config.DEFAULT_DISEASE_LAYER
    min_retrieval_confidence: float = src_config.MIN_RETRIEVAL_CONFIDENCE
    retrieval_top_k: int = src_config.RETRIEVAL_TOP_K


@lru_cache(maxsize=1)
def get_settings() -> BackendSettings:
    return BackendSettings()


def dependency_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def readiness() -> dict[str, Any]:
    """Return environment readiness without secret values."""
    layers = {row["layer"]: row for row in layer_status_rows()}
    return {
        "backend_running": True,
        "environment": get_settings().environment,
        "dependencies": {
            "fastapi": dependency_available("fastapi"),
            "pydantic": dependency_available("pydantic"),
            "supabase": dependency_available("supabase"),
            "google_genai": dependency_available("google.genai") or dependency_available("google"),
        },
        "configuration": {
            "supabase_url_configured": bool(src_config.SUPABASE_URL),
            "supabase_anon_key_configured": bool(src_config.SUPABASE_ANON_KEY),
            "supabase_service_role_configured": bool(src_config.SUPABASE_SERVICE_ROLE_KEY),
            "gemini_configured": bool(src_config.GEMINI_API_KEYS),
            "gemini_key_count": len(src_config.GEMINI_API_KEYS),
            "generation_models_configured": bool(src_config.GEMINI_GENERATION_MODELS),
            "embedding_provider": src_config.EMBEDDING_PROVIDER,
            "embedding_dim": src_config.EMBEDDING_DIM,
            "embedding_api_url_configured": bool(src_config.EMBEDDING_API_URL),
            "embedding_api_style": src_config.EMBEDDING_API_STYLE,
            "embedding_api_model": src_config.EMBEDDING_API_MODEL,
            "chunks_table": src_config.CHUNKS_TABLE,
            "match_function": src_config.MATCH_FUNCTION,
            "generation_provider": src_config.LLM_PROVIDER,
        },
        "runtime": {
            "retrieval_mode": "supabase_pgvector" if src_config.SUPABASE_URL and src_config.SUPABASE_ANON_KEY else "local_lexical_fallback",
            "generation_mode": "gemini" if src_config.GEMINI_API_KEYS else "deterministic_fallback",
            "active_disease_layer_is_diabetes": bool(layers.get("diabetes", {}).get("active")),
        },
    }
