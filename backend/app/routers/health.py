from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings, readiness


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "readiness": readiness(),
    }
