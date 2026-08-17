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


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),
    os.getenv("GEMINI_API_KEY_1", ""),
    os.getenv("GEMINI_API_KEY_2", ""),
    os.getenv("GEMINI_API_KEY_3", ""),
]
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")
GEMINI_GENERATION_MODELS = _csv("GEMINI_GENERATION_MODELS", "gemini-2.0-flash,gemini-1.5-flash")
GEMINI_EMBEDDING_MODELS = _csv("GEMINI_EMBEDDING_MODELS", "gemini-embedding-001")
GEMINI_GENERATION_MODEL = GEMINI_GENERATION_MODELS[0]
GEMINI_EMBEDDING_MODEL = GEMINI_EMBEDDING_MODELS[0]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

EMBEDDING_DIM = _int("EMBEDDING_DIM", 1536)
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
    """Small YAML reader for this repo's simple config files.

    PyYAML is intentionally not required. If PyYAML is installed it is used;
    otherwise this handles key/value, simple nesting, lists, ints, floats,
    booleans, and quoted/unquoted strings used by our config files.
    """
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
        "retry_attempts": 2,
        "retry_backoff_seconds": 0.75,
        "generation_temperature": 0.2,
        "max_output_tokens": 2048,
        "log_file": "data/evaluation/ai_fallback_logs.jsonl",
    }
    path = project_path("config", "fallback.yaml")
    if path.exists():
        defaults.update(parse_simple_yaml(path))
    return defaults
