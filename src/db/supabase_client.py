from __future__ import annotations

from src.core.config import SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from src.core.errors import ConfigurationError


def _require_url() -> None:
    if not SUPABASE_URL:
        raise ConfigurationError("SUPABASE_URL must be set.")


def get_admin_client():
    _require_url()
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ConfigurationError("SUPABASE_SERVICE_ROLE_KEY must be set for indexing/logging.")
    try:
        from supabase import create_client
    except Exception as exc:
        raise ConfigurationError("supabase is not installed. Run `pip install -r requirements.txt`.") from exc
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_client():
    _require_url()
    if not SUPABASE_ANON_KEY:
        raise ConfigurationError("SUPABASE_ANON_KEY must be set for retrieval.")
    try:
        from supabase import create_client
    except Exception as exc:
        raise ConfigurationError("supabase is not installed. Run `pip install -r requirements.txt`.") from exc
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def supabase_configured(*, admin: bool = False) -> bool:
    if admin:
        return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


from src.core.config import MATCH_FUNCTION


def match_chunks(
    query_embedding: list[float],
    clinical_topic: str,
    disease_layer: str,
    top_k: int = 5,
) -> list[dict]:
    client = get_client()

    response = client.rpc(
        MATCH_FUNCTION,
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_clinical_topic": clinical_topic,
            "filter_disease_layer": disease_layer,
        },
    ).execute()

    return response.data or []
