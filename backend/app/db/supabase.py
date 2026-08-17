from __future__ import annotations

from src.db.supabase_client import get_client, supabase_configured


def get_public_supabase_client():
    """Return anon-key client for API read paths.

    Service role access remains reserved for ingestion/admin scripts.
    """
    return get_client()


def is_supabase_ready() -> bool:
    return supabase_configured(admin=False)
