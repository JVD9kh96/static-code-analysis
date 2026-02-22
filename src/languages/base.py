"""
Abstract base for language profiles.

Each profile encapsulates every language-specific aspect of the evaluation
pipeline: which tools to run, how to filter results, how to build prompts,
and how to calculate the final score.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set


class LanguageProfile(ABC):
    """Contract that every language plug-in must satisfy."""

    # ── metadata ──────────────────────────────────────────────────────
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable language name (e.g. ``'Python'``)."""

    @property
    @abstractmethod
    def extensions(self) -> Set[str]:
        """File extensions including the dot (e.g. ``{'.py'}``). """

    # ── deterministic tools ───────────────────────────────────────────
    @abstractmethod
    def run_tools(self, file_path: str) -> Dict[str, Any]:
        """Run all deterministic tools and return a dict keyed by tool name."""

    @abstractmethod
    def filter_lint(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        """Return a filtered / noise-reduced copy of the lint results."""

    # ── RAG ────────────────────────────────────────────────────────────
    @abstractmethod
    def derive_rag_queries(self, source_code: str) -> List[str]:
        """Extract topics from source code to query the RAG knowledge base."""

    # ── prompts ────────────────────────────────────────────────────────
    @property
    @abstractmethod
    def detective_system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def judge_system_prompt(self) -> str: ...

    @abstractmethod
    def build_detective_user(
        self,
        file_path: str,
        source_code: str,
        tools: Dict[str, Any],
        rag_chunks: List[str],
    ) -> str:
        """Format the Detective's user message from tool results + RAG."""

    @abstractmethod
    def build_judge_user(
        self,
        file_path: str,
        source_code: str,
        potential_issues: List[Dict[str, Any]],
        tools: Dict[str, Any],
    ) -> str:
        """Format the Judge's user message from Detective findings + tools."""

    # ── scoring ────────────────────────────────────────────────────────
    @abstractmethod
    def calculate_score(
        self,
        verified_violations: List[Dict[str, Any]],
        tools: Dict[str, Any],
    ) -> int:
        """Compute a deterministic score in [0, 100]."""
