from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from src.core import config
from src.core.errors import ConfigurationError, ModelFallbackExhausted
from src.core.logging import log_ai_operation

QUOTA_HINTS = (
    "quota",
    "rate",
    "429",
    "resource_exhausted",
    "too many requests",
)
CREDENTIAL_HINTS = (
    "403",
    "permission_denied",
    "permission denied",
    "denied access",
    "api key not valid",
    "invalid api key",
    "unauthorized",
    "authentication",
)
MODEL_HINTS = (
    "404",
    "not found",
    "invalid model",
    "unsupported model",
    "model is not supported",
)
TRANSIENT_HINTS = (
    "timeout",
    "temporarily",
    "connection",
    "network",
    "deadline",
    "503",
    "500",
    "internal",
)


@dataclass
class AttemptFailure:
    model: str
    operation_type: str
    error_type: str
    message: str
    key_pool: str | None = None
    key_index: int | None = None


def _classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if any(h in message for h in CREDENTIAL_HINTS):
        return "credential_permission_error"
    if any(h in message for h in QUOTA_HINTS):
        return "transient_or_quota"
    if any(h in message for h in MODEL_HINTS):
        return "model_unavailable"
    if any(h in message for h in TRANSIENT_HINTS):
        return "transient_or_quota"
    return exc.__class__.__name__


class GeminiFallbackRouter:
    def __init__(self) -> None:
        self.embedding_keys = config.GEMINI_EMBEDDING_API_KEYS
        self.generation_keys = config.GEMINI_GENERATION_API_KEYS
        self.generation_models = config.GEMINI_GENERATION_MODELS
        self.embedding_models = config.GEMINI_EMBEDDING_MODELS
        self.embedding_dim = config.EMBEDDING_DIM
        self.settings = config.load_fallback_config()

        if not self.embedding_keys and not self.generation_keys:
            raise ConfigurationError(
                "No Gemini keys configured. Add GEMINI_EMBEDDING_API_KEY_0 and/or GEMINI_GENERATION_API_KEY_0."
            )

    def _clients(self, keys: list[str]) -> Iterable[tuple[int, object]]:
        try:
            from google import genai
        except Exception as exc:
            raise ConfigurationError("google-genai is not installed. Run `pip install -r requirements.txt`.") from exc
        for index, key in enumerate(keys):
            if key:
                yield index, genai.Client(api_key=key)

    def embed_text(self, text: str, kind: str = "document") -> list[float]:
        embeddings = self.embed_batch([text], kind=kind)
        return embeddings[0]

    def embed_batch(self, texts: list[str], kind: str = "document") -> list[list[float]]:
        if not texts or any(not (t or "").strip() for t in texts):
            raise ValueError("Cannot embed empty text.")
        if not self.embedding_keys:
            raise ConfigurationError("No Gemini embedding keys configured.")

        failures: list[AttemptFailure] = []
        backoff = float(self.settings.get("retry_backoff_seconds", 0.75))
        retry_attempts = int(self.settings.get("retry_attempts", 1))

        for model in self.embedding_models:
            model_failed = False
            for key_index, client in self._clients(self.embedding_keys):
                for attempt in range(retry_attempts + 1):
                    start = time.perf_counter()
                    try:
                        vectors = self._embed_batch_once(client, model, texts, kind)
                        if len(vectors) != len(texts):
                            vectors = [self._embed_one_once(client, model, t, kind) for t in texts]
                        self._validate_vectors(vectors)
                        log_ai_operation(
                            provider="gemini",
                            model=model,
                            operation_type="embedding",
                            success=True,
                            latency_ms=(time.perf_counter() - start) * 1000,
                            log_file=self.settings["log_file"],
                            key_pool="embedding",
                            key_index=key_index,
                        )
                        return vectors
                    except Exception as exc:
                        error_type = _classify_error(exc)
                        failures.append(
                            AttemptFailure(model, "embedding", error_type, str(exc)[:250], "embedding", key_index)
                        )
                        log_ai_operation(
                            provider="gemini",
                            model=model,
                            operation_type="embedding",
                            success=False,
                            latency_ms=(time.perf_counter() - start) * 1000,
                            error_type=error_type,
                            log_file=self.settings["log_file"],
                            key_pool="embedding",
                            key_index=key_index,
                        )

                        if error_type == "model_unavailable":
                            model_failed = True
                            break
                        if error_type == "credential_permission_error":
                            # This key is not usable for embeddings. Try next key.
                            break
                        if error_type == "transient_or_quota" and attempt < retry_attempts:
                            time.sleep(backoff * (attempt + 1))
                            continue
                        # quota/transient exhausted for this key: try the next key.
                        break
                if model_failed:
                    break
        raise ModelFallbackExhausted(f"All Gemini embedding fallbacks failed: {failures}")

    def _embed_batch_once(self, client: object, model: str, texts: list[str], kind: str) -> list[list[float]]:
        from google.genai import types

        task_type = "RETRIEVAL_DOCUMENT" if kind == "document" else "RETRIEVAL_QUERY"
        response = client.models.embed_content(
            model=model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.embedding_dim),
        )
        return [list(item.values) for item in (response.embeddings or [])]

    def _embed_one_once(self, client: object, model: str, text: str, kind: str) -> list[float]:
        from google.genai import types

        task_type = "RETRIEVAL_DOCUMENT" if kind == "document" else "RETRIEVAL_QUERY"
        response = client.models.embed_content(
            model=model,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.embedding_dim),
        )
        if not response.embeddings:
            raise RuntimeError("Gemini returned no embeddings.")
        return list(response.embeddings[0].values)

    def _validate_vectors(self, vectors: list[list[float]]) -> None:
        for idx, vector in enumerate(vectors, start=1):
            if len(vector) != self.embedding_dim:
                raise RuntimeError(
                    f"Embedding dimension mismatch for item {idx}. Expected {self.embedding_dim}, got {len(vector)}."
                )

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        if not self.generation_keys:
            # Last-resort: allow embedding keys to generate only if no generation pool exists.
            # Prefer configuring GEMINI_GENERATION_API_KEY_0..N.
            if not self.embedding_keys:
                raise ConfigurationError("No Gemini generation keys configured.")
            generation_keys = self.embedding_keys
            key_pool = "embedding_fallback_for_generation"
        else:
            generation_keys = self.generation_keys
            key_pool = "generation"

        failures: list[AttemptFailure] = []
        retry_attempts = int(self.settings.get("retry_attempts", 1))
        backoff = float(self.settings.get("retry_backoff_seconds", 0.75))
        temp = self.settings.get("generation_temperature", 0.2) if temperature is None else temperature
        output_tokens = int(max_output_tokens or self.settings.get("max_output_tokens", 2048))

        for model in self.generation_models:
            model_failed = False
            for key_index, client in self._clients(generation_keys):
                for attempt in range(retry_attempts + 1):
                    start = time.perf_counter()
                    try:
                        from google.genai import types

                        response = client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=temp,
                                max_output_tokens=output_tokens,
                            ),
                        )
                        text = (response.text or "").strip()
                        if not text:
                            raise RuntimeError("Gemini returned an empty response.")
                        log_ai_operation(
                            provider="gemini",
                            model=model,
                            operation_type="generation",
                            success=True,
                            latency_ms=(time.perf_counter() - start) * 1000,
                            log_file=self.settings["log_file"],
                            key_pool=key_pool,
                            key_index=key_index,
                        )
                        return text
                    except Exception as exc:
                        error_type = _classify_error(exc)
                        failures.append(
                            AttemptFailure(model, "generation", error_type, str(exc)[:250], key_pool, key_index)
                        )
                        log_ai_operation(
                            provider="gemini",
                            model=model,
                            operation_type="generation",
                            success=False,
                            latency_ms=(time.perf_counter() - start) * 1000,
                            error_type=error_type,
                            log_file=self.settings["log_file"],
                            key_pool=key_pool,
                            key_index=key_index,
                        )

                        if error_type == "model_unavailable":
                            model_failed = True
                            break
                        if error_type == "credential_permission_error":
                            break
                        if error_type == "transient_or_quota" and attempt < retry_attempts:
                            time.sleep(backoff * (attempt + 1))
                            continue
                        break
                if model_failed:
                    break
        raise ModelFallbackExhausted(f"All Gemini generation fallbacks failed: {failures}")


def get_router() -> GeminiFallbackRouter:
    return GeminiFallbackRouter()
