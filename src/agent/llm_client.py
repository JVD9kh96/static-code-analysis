"""
Thread-safe, synchronous client for any OpenAI-compatible chat-completions
endpoint (Gemma, DeepSeek, LLaMA, Mistral, etc.).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

import requests

from src.utils.config import settings

logger = logging.getLogger(__name__)

# Re-usable session per thread (connection-pooling friendly).
_thread_local = threading.local()


def _get_session() -> requests.Session:
    """Return a per-thread ``requests.Session``."""
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
    return _thread_local.session


class LLMClient:
    """
    Synchronous, thread-safe wrapper around any OpenAI-compatible
    ``/v1/chat/completions`` endpoint.

    * Each thread gets its own ``requests.Session`` (connection pooling).
    * Automatic retries with exponential back-off on transient errors.
    * Model-agnostic: swap ``LLM_API_URL`` and ``LLM_MODEL`` env vars to
      point at any compatible backend (Gemma, DeepSeek, Ollama, vLLM …).
    """

    def __init__(
        self,
        api_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_url = api_url or settings.llm_api_url
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries if max_retries is not None else settings.llm_max_retries

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send *messages* to the LLM endpoint and return the assistant's
        reply as a plain string.

        Raises ``RuntimeError`` if all retries are exhausted.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                session = _get_session()
                response = session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if not content:
                    raise ValueError("Empty content in LLM response.")
                return content

            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError,
                ValueError,
            ) as exc:
                last_error = exc
                wait = min(2 ** attempt, 16)
                logger.warning(
                    "LLM API attempt %d/%d failed (%s). Retrying in %ds …",
                    attempt,
                    self.max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)

        raise RuntimeError(
            f"LLM API failed after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )
