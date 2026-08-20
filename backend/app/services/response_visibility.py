from __future__ import annotations

from copy import deepcopy
from typing import Any


def apply_response_visibility(
    pipeline_result: dict[str, Any],
    show_chunks: bool,
) -> dict[str, Any]:
    """
    Hide retrieval chunks only after:
    - retrieval
    - generation
    - citation validation
    - unsupported claim validation

    Never mutate the original pipeline result.
    """
    response = deepcopy(pipeline_result)

    if not show_chunks:
        retrieval = response.get("retrieval")

        if isinstance(retrieval, dict):
            retrieval["chunks"] = []

        if "chunks" in response and isinstance(response["chunks"], list):
            response["chunks"] = []

    return response
