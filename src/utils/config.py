"""
Configuration loader for the Agentic Static Code Evaluator.

Centralizes all runtime settings: API endpoints, model parameters,
paths, and thread pool sizes. Values can be overridden via environment
variables so that nothing is hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project root (two levels up from this file → src/utils/config.py)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Immutable, thread-safe configuration object."""

    # ── LLM API (any OpenAI-compatible endpoint) ────────────────────
    llm_api_url: str = os.getenv(
        "LLM_API_URL",
        "http://87.236.166.36:8082/v1/chat/completions",
    )
    llm_model: str = os.getenv("LLM_MODEL", "gemma")

    # llm_api_url: str = os.getenv(
    #     "LLM_API_URL",
    #     "http://87.236.166.36:8083/v1/chat/completions",
    # )
    # llm_model: str = os.getenv("LLM_MODEL", "deepseek")

    # llm_api_url: str = os.getenv(
    #     "LLM_API_URL",
    #     "http://87.236.166.36:8084/v1/chat/completions",
    # )
    # llm_model: str = os.getenv("LLM_MODEL", "Qwen")

    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "120"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))

    # ── RAG / Embeddings ──────────────────────────────────────────────
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    chroma_persist_dir: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        str(_PROJECT_ROOT / ".chromadb"),
    )
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "guidelines")
    knowledge_base_path: str = os.getenv(
        "KNOWLEDGE_BASE_PATH",
        str(_PROJECT_ROOT / "knowledge_base"),
    )
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "3"))

    # ── Concurrency ───────────────────────────────────────────────────
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))

    # ── Paths ─────────────────────────────────────────────────────────
    project_root: str = str(_PROJECT_ROOT)


# Singleton instance – import this everywhere.
settings = Settings()
