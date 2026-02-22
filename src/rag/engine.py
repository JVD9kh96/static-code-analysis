"""
RAG engine – ingests Markdown guidelines into ChromaDB and retrieves
the most relevant chunks for a given query.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List

import chromadb

from src.rag.embeddings import LocalEmbeddingFunction
from src.utils.config import settings

logger = logging.getLogger(__name__)


class RuleRetriever:
    """Manages a ChromaDB collection of coding-guideline chunks."""

    def __init__(self) -> None:
        self._ef = LocalEmbeddingFunction()
        self._client = chromadb.Client(
            chromadb.config.Settings(
                anonymized_telemetry=False,
                is_persistent=True,
                persist_directory=settings.chroma_persist_dir,
            )
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            embedding_function=self._ef,
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest(self, directory: str | None = None) -> int:
        """
        Read every ``*.md`` file under *directory* (default:
        ``knowledge_base/``), split by ``## `` headers, and upsert
        chunks into ChromaDB.

        Returns the number of chunks upserted.
        """
        kb_path = Path(directory or settings.knowledge_base_path)
        if not kb_path.exists():
            logger.warning("Knowledge-base path does not exist: %s", kb_path)
            return 0

        md_files = list(kb_path.rglob("*.md"))
        if not md_files:
            logger.warning("No .md files found in %s", kb_path)
            return 0

        all_chunks: List[Dict[str, str]] = []
        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            chunks = self._split_by_headers(text, source=str(md_file))
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        ids = [c["id"] for c in all_chunks]
        documents = [c["text"] for c in all_chunks]
        metadatas = [{"source": c["source"], "header": c["header"]} for c in all_chunks]

        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Upserted %d guideline chunks into ChromaDB.", len(all_chunks))
        return len(all_chunks)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: int | None = None) -> List[str]:
        """
        Return the *top_k* most relevant guideline chunks for *query*.
        """
        k = top_k or settings.rag_top_k
        results = self._collection.query(query_texts=[query], n_results=k)
        documents: List[str] = []
        if results and results["documents"]:
            documents = results["documents"][0]  # first (and only) query
        return documents

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_by_headers(text: str, source: str) -> List[Dict[str, str]]:
        """
        Split a Markdown string on ``## `` boundaries.  Each resulting
        chunk keeps its header as the first line.
        """
        # Split on lines that start with "## "
        sections = re.split(r"(?m)^(?=## )", text)
        chunks: List[Dict[str, str]] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            # Extract header (first line)
            first_line = section.split("\n", 1)[0].strip().lstrip("#").strip()
            chunk_id = hashlib.sha256(section.encode()).hexdigest()[:16]
            chunks.append(
                {
                    "id": chunk_id,
                    "header": first_line,
                    "text": section,
                    "source": source,
                }
            )
        return chunks
