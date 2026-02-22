"""
Local embedding wrapper around *sentence-transformers*.

Provides a thin, reusable interface that ChromaDB (and anything else)
can call without knowing the underlying model details.
"""

from __future__ import annotations

import logging
from typing import List

from chromadb.api.types import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer

from src.utils.config import settings

logger = logging.getLogger(__name__)


class LocalEmbeddingFunction(EmbeddingFunction[List[str]]):
    """
    ChromaDB-compatible embedding function backed by a local
    sentence-transformers model.

    The model is loaded lazily on first call so that import-time cost is zero.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    # -- lazy loader --------------------------------------------------------
    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model '%s' …", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    # -- ChromaDB interface -------------------------------------------------
    def __call__(self, input: List[str]) -> Embeddings:  # noqa: A002
        """Embed a list of texts and return a list of float-vectors."""
        model = self._load_model()
        embeddings = model.encode(input, show_progress_bar=False)
        return embeddings.tolist()
