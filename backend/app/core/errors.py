from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.core.errors import RagError


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "api_error") -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RagError)
    async def rag_error_handler(request: Request, exc: RagError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=502,
            content={"error": {"code": exc.__class__.__name__, "message": str(exc)}},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": exc.errors()}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_server_error", "message": exc.__class__.__name__}},
        )
