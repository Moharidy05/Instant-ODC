from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECRET_FIELD_HINTS = ("key", "token", "secret", "password")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if any(h in k.lower() for h in SECRET_FIELD_HINTS) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_record = redact(record)
    safe_record.setdefault("timestamp", utc_now_iso())
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe_record, ensure_ascii=False) + "\n")


def log_ai_operation(
    *,
    provider: str,
    model: str,
    operation_type: str,
    success: bool,
    latency_ms: float,
    error_type: str | None = None,
    log_file: str | Path = "data/evaluation/ai_fallback_logs.jsonl",
    key_index: int | None = None,
    key_pool: str | None = None,
) -> None:
    record = {
        "provider": provider,
        "model": model,
        "operation_type": operation_type,
        "success": success,
        "latency_ms": round(latency_ms, 2),
        "error_type": error_type,
    }
    if key_index is not None:
        record["key_index"] = key_index
    if key_pool:
        record["key_pool"] = key_pool
    append_jsonl(log_file, record)
