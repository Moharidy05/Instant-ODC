from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.core.logging import append_jsonl


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        append_jsonl(
            "data/evaluation/backend_request_logs.jsonl",
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "client": request.client.host if request.client else None,
            },
        )
