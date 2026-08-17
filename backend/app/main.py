from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import request_logging_middleware
from backend.app.routers import ask, evidence, evaluation, foods, health, layers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-style API for evidence-grounded diabetes food safety RAG. "
            "Use /docs for OpenAPI documentation."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_logging_middleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(layers.router)
    app.include_router(ask.router)
    app.include_router(foods.router)
    app.include_router(evidence.router)
    app.include_router(evaluation.router)
    return app


app = create_app()
