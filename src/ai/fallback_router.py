from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from src.core import config
from src.core.errors import ConfigurationError, ModelFallbackExhausted
from src.core.logging import log_ai_operation


TRANSIENT_HINTS = (
    "quota",
    "rate",
    "429",
    "resource_exhausted",
    "timeout",
    "temporarily",
    "unavailable",
    "connection",
    "network",
    "deadline",
    "503",
    "500",
)
MODEL_HINTS = ("not found", "invalid model", "unsupported", "permission", "404")


@dataclass
class AttemptFailure:
    model: str
    operation_type: str
    error_type: str
    message: str


def _classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if any(h in message for h in MODEL_HINTS):
        return "model_unavailable"
    if any(h in message for h in TRANSIENT_HINTS):
        return "transient_or_quota"
    return exc.__class__.__name__


class GeminiFallbackRouter:
    def __init__(self) -> None:
        self.keys = config.GEMINI_API_KEYS
        self.generation_models = config.GEMINI_GENERATION_MODELS
        self.embedding_models = config.GEMINI_EMBEDDING_MODELS
        self.embedding_dim = config.EMBEDDING_DIM
        self.settings = config.load_fallback_config()
        if not self.keys:
            raise ConfigurationError("At least one GEMINI_API_KEY value must be configured.")

    def _clients(self) -> Iterable[object]:
        try:
            from google import genai
        except Exception as exc:
            raise ConfigurationError("google-genai is not installed. Run `pip install -r requirements.txt`.") from exc
        for key in self.keys:
            yield genai.Client(api_key=key)

    def embed_text(self, text: str, kind: str = "document") -> list[float]:
        embeddings = self.embed_batch([text], kind=kind)
        return embeddings[0]

    def embed_batch(self, texts: list[str], kind: str = "document") -> list[list[float]]:
        if not texts or any(not (t or "").strip() for t in texts):
            raise ValueError("Cannot embed empty text.")

        failures: list[AttemptFailure] = []
        for model in self.embedding_models:
            for client in self._clients():
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
                    )
                    return vectors
                except Exception as exc:
                    error_type = _classify_error(exc)
                    failures.append(AttemptFailure(model, "embedding", error_type, str(exc)[:250]))
                    log_ai_operation(
                        provider="gemini",
                        model=model,
                        operation_type="embedding",
                        success=False,
                        latency_ms=(time.perf_counter() - start) * 1000,
                        error_type=error_type,
                        log_file=self.settings["log_file"],
                    )
                    if error_type == "model_unavailable":
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
                    f"Embedding dimension mismatch for item {idx}. "
                    f"Expected {self.embedding_dim}, got {len(vector)}."
                )

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        failures: list[AttemptFailure] = []
        retry_attempts = int(self.settings.get("retry_attempts", 2))
        backoff = float(self.settings.get("retry_backoff_seconds", 0.75))
        temp = self.settings.get("generation_temperature", 0.2) if temperature is None else temperature
        output_tokens = int(max_output_tokens or self.settings.get("max_output_tokens", 2048))

        for model in self.generation_models:
            for client in self._clients():
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
                        )
                        return text
                    except Exception as exc:
                        error_type = _classify_error(exc)
                        failures.append(AttemptFailure(model, "generation", error_type, str(exc)[:250]))
                        log_ai_operation(
                            provider="gemini",
                            model=model,
                            operation_type="generation",
                            success=False,
                            latency_ms=(time.perf_counter() - start) * 1000,
                            error_type=error_type,
                            log_file=self.settings["log_file"],
                        )
                        if error_type == "model_unavailable":
                            break
                        if attempt < retry_attempts and error_type == "transient_or_quota":
                            time.sleep(backoff * (attempt + 1))
                            continue
                        break
        raise ModelFallbackExhausted(f"All Gemini generation fallbacks failed: {failures}")


def get_router() -> GeminiFallbackRouter:
    return GeminiFallbackRouter()
