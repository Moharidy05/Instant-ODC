from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _csv(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        value = (value or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _collect_numbered_env(base_name: str, max_keys: int = 60, include_plain: bool = True) -> list[str]:
    """Collect NAME, NAME_0, NAME_1 ... without logging their values."""
    values: list[str] = []
    if include_plain:
        values.append(os.getenv(base_name, ""))
    for i in range(max_keys):
        values.append(os.getenv(f"{base_name}_{i}", ""))
    return _dedupe(values)


def _split_legacy_gemini_keys() -> tuple[list[str], list[str]]:
    """Fallback: split old GEMINI_API_KEY* keys into embedding/generation pools."""
    legacy = _collect_numbered_env("GEMINI_API_KEY", max_keys=60, include_plain=True)
    if not legacy:
        return [], []
    if len(legacy) == 1:
        # Last-resort fallback only: one key can do both operations.
        return legacy, legacy
    mid = max(1, len(legacy) // 2)
    return legacy[:mid], legacy[mid:]


def get_gemini_embedding_keys() -> list[str]:
    explicit = _collect_numbered_env("GEMINI_EMBEDDING_API_KEY", max_keys=60, include_plain=True)
    if explicit:
        return explicit
    embedding_keys, _ = _split_legacy_gemini_keys()
    return embedding_keys


def get_gemini_generation_keys() -> list[str]:
    explicit = _collect_numbered_env("GEMINI_GENERATION_API_KEY", max_keys=60, include_plain=True)
    if explicit:
        return explicit
    _, generation_keys = _split_legacy_gemini_keys()
    return generation_keys


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "embeddinggemma_api").strip().lower()

# Explicit pools used by the fallback router.
GEMINI_EMBEDDING_API_KEYS = get_gemini_embedding_keys()
GEMINI_GENERATION_API_KEYS = get_gemini_generation_keys()

# Backward-compatible name used by old checks/UI.
GEMINI_API_KEYS = _dedupe(GEMINI_EMBEDDING_API_KEYS + GEMINI_GENERATION_API_KEYS)
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

GEMINI_GENERATION_MODELS = _csv("GEMINI_GENERATION_MODELS", "gemini-2.0-flash,gemini-1.5-flash")
GEMINI_EMBEDDING_MODELS = _csv("GEMINI_EMBEDDING_MODELS", "gemini-embedding-001")
GEMINI_GENERATION_MODEL = GEMINI_GENERATION_MODELS[0]
GEMINI_EMBEDDING_MODEL = GEMINI_EMBEDDING_MODELS[0]

LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
LOCAL_EMBEDDING_FALLBACK_MODEL = os.getenv(
    "LOCAL_EMBEDDING_FALLBACK_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

EMBEDDING_DIM = _int("EMBEDDING_DIM", 768)
EMBEDDING_BATCH_SIZE = _int("EMBEDDING_BATCH_SIZE", 10 if EMBEDDING_PROVIDER == "gemini" else 32)
EMBEDDING_SLEEP_SECONDS = _float("EMBEDDING_SLEEP_SECONDS", 2.0 if EMBEDDING_PROVIDER == "gemini" else 0.5)
GEMINI_MAX_RETRIES_PER_KEY = _int("GEMINI_MAX_RETRIES_PER_KEY", 1)

EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:11341/api/embed").strip()
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "").strip()
EMBEDDING_API_TIMEOUT_SECONDS = _int("EMBEDDING_API_TIMEOUT_SECONDS", 60)
EMBEDDING_API_STYLE = os.getenv("EMBEDDING_API_STYLE", "ollama").strip().lower()
EMBEDDING_API_MODEL = os.getenv("EMBEDDING_API_MODEL", "embeddinggemma").strip()

CHUNKS_TABLE = os.getenv("CHUNKS_TABLE", "guideline_chunks").strip()
MATCH_FUNCTION = os.getenv("MATCH_FUNCTION", "match_guideline_chunks").strip()

PDF_PATH = os.getenv("PDF_PATH", "data/raw/dc26s005.pdf")
PROJECT_TOPIC = os.getenv("PROJECT_TOPIC", "diabetes_food_safety")
DEFAULT_DISEASE_LAYER = os.getenv("DEFAULT_DISEASE_LAYER", "diabetes")
RETRIEVAL_TOP_K = _int("RETRIEVAL_TOP_K", 5)
RETRIEVAL_CANDIDATE_K = _int("RETRIEVAL_CANDIDATE_K", 20)
MIN_RETRIEVAL_CONFIDENCE = _float("MIN_RETRIEVAL_CONFIDENCE", 0.55)

DOCUMENT_ID = "ada_standards_2026_section_5"
DOCUMENT_TITLE = "ADA Standards of Care in Diabetes 2026 - Section 5"
SOURCE_FILE = "dc26s005.pdf"


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


def parse_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Small YAML reader for this repo's simple config files."""
    try:
        import yaml  # type: ignore

        with Path(path).open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        pass

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)
    return root


def _parse_scalar(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except Exception:
            return [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip("'\"")


def load_retrieval_config() -> dict[str, Any]:
    defaults = {
        "chunk_target_min": 700,
        "chunk_target_max": 1200,
        "overlap_chars": 150,
        "candidate_k": RETRIEVAL_CANDIDATE_K,
        "top_k_options": [3, 5, 8, 10],
    }
    path = project_path("config", "retrieval.yaml")
    if path.exists():
        defaults.update(parse_simple_yaml(path))
    return defaults


def load_fallback_config() -> dict[str, Any]:
    defaults = {
        "provider": "gemini",
        "retry_attempts": GEMINI_MAX_RETRIES_PER_KEY,
        "retry_backoff_seconds": 0.75,
        "generation_temperature": 0.2,
        "max_output_tokens": 2048,
        "log_file": "data/evaluation/ai_fallback_logs.jsonl",
    }
    path = project_path("config", "fallback.yaml")
    if path.exists():
        defaults.update(parse_simple_yaml(path))
    return defaults
