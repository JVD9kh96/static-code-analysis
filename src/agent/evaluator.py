"""
The Evaluator – Multi-Agent "Detective → Judge → Refiner" Reflection Architecture.

Orchestrates the full pipeline for a single file, **language-agnostic**:

1. Detect the language and obtain the matching ``LanguageProfile``.
2. Run deterministic static-analysis tools (profile-specific).
3. Retrieve RAG guidelines (if enabled).
4. Agent A (Detective): source + tool results + RAG → potential_issues.
5. Agent B (Judge): source + potential_issues + filtered tools → verified_violations.
6. Agent C (Refiner): if Judge JSON fails to parse, attempt repair.
7. Deterministic Scoring Engine: score = 100 − penalties, clamped 0–100.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.agent.llm_client import LLMClient
from src.agent.prompts import REFINER_SYSTEM_PROMPT, REFINER_USER_TEMPLATE
from src.languages import detect_profile

if TYPE_CHECKING:
    from src.languages.base import LanguageProfile
    from src.rag.engine import RuleRetriever

logger = logging.getLogger(__name__)

# Sentinel value for parse failures
SCORE_NOT_AVAILABLE = "N/A"


class Evaluator:
    """
    Evaluates a single source file through the Detective → Judge pipeline.

    The class is **thread-safe**: each instance holds only immutable or
    per-call state, and the ``LLMClient`` it wraps uses per-thread
    sessions internally.

    Parameters
    ----------
    llm_client : LLMClient
        The (model-agnostic) LLM chat client.
    rule_retriever : RuleRetriever | None
        The RAG retriever. Pass ``None`` to bypass RAG entirely.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        rule_retriever: Optional["RuleRetriever"] = None,
    ) -> None:
        self._llm = llm_client
        self._rag = rule_retriever

    @property
    def rag_enabled(self) -> bool:
        return self._rag is not None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def evaluate(self, file_path: str) -> Dict[str, Any]:
        """
        Run the Detective → Judge → Scoring pipeline on *file_path*.

        Returns a dict with keys: ``file``, ``language``, ``score``,
        ``violations``, ``summary``, and ``error`` (if something went wrong).
        """
        path = Path(file_path)
        if not path.exists():
            return self._error_result(file_path, "File not found.")

        # Detect language
        profile = detect_profile(file_path)
        if profile is None:
            return self._error_result(
                file_path,
                f"Unsupported file type: '{path.suffix}'.",
            )

        source_code = path.read_text(encoding="utf-8", errors="replace")
        if not source_code.strip():
            return self._error_result(file_path, "File is empty.")

        # 1. Run deterministic tools (language-specific)
        logger.info("[%s] Running %s static analysis …", path.name, profile.name)
        tools = profile.run_tools(file_path)

        # 2. Retrieve RAG rules (if enabled)
        rag_chunks: List[str] = []
        if self.rag_enabled:
            queries = profile.derive_rag_queries(source_code)
            rag_chunks = self._fetch_rag_context(queries)
        else:
            logger.debug("[%s] RAG bypassed.", path.name)

        # 3. The Detective
        logger.info("[%s] Detective agent – scanning …", path.name)
        detective_user = profile.build_detective_user(
            file_path=file_path,
            source_code=source_code,
            tools=tools,
            rag_chunks=rag_chunks,
        )
        try:
            detective_response = self._llm.chat(
                messages=[
                    {"role": "system", "content": profile.detective_system_prompt},
                    {"role": "user", "content": detective_user},
                ]
            )
        except RuntimeError as exc:
            return self._error_result(file_path, f"LLM error (Detective): {exc}")

        potential_issues = self._parse_json_list(detective_response)

        # 4. The Judge
        logger.info("[%s] Judge agent – filtering …", path.name)
        judge_user = profile.build_judge_user(
            file_path=file_path,
            source_code=source_code,
            potential_issues=potential_issues,
            tools=tools,
        )
        try:
            judge_response = self._llm.chat(
                messages=[
                    {"role": "system", "content": profile.judge_system_prompt},
                    {"role": "user", "content": judge_user},
                ]
            )
        except RuntimeError as exc:
            return self._error_result(file_path, f"LLM error (Judge): {exc}")

        verified_data, parse_error = self._parse_judge_response_with_refiner(
            judge_response, path.name
        )

        # 6. Deterministic Scoring (language-specific)
        if parse_error:
            final_score = SCORE_NOT_AVAILABLE
        else:
            final_score = profile.calculate_score(
                verified_data.get("verified_violations", []),
                tools,
            )

        return {
            "file": file_path,
            "language": profile.name,
            "score": final_score,
            "violations": verified_data.get("verified_violations", []),
            "summary": verified_data.get("analysis_summary", ""),
            "reliability_analysis": verified_data.get("analysis_summary", ""),
            "maintainability_analysis": "",
            "parse_error": parse_error,
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_json_response(raw: str) -> str:
        """Remove markdown fences and whitespace from LLM JSON output."""
        return re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")

    @staticmethod
    def _parse_json_list(raw: str) -> List[Dict[str, Any]]:
        cleaned = Evaluator._clean_json_response(raw)
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def _try_parse_judge_json(cleaned: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempt to parse Judge JSON.
        Returns (parsed_data, None) on success, or (None, error_message) on failure.
        """
        try:
            data = json.loads(cleaned)
            return {
                "verified_violations": data.get("verified_violations", []),
                "analysis_summary": data.get("analysis_summary", ""),
            }, None
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            return None, str(exc)

    def _parse_judge_response_with_refiner(
        self, raw: str, file_name: str
    ) -> tuple[Dict[str, Any], bool]:
        """
        Parse Judge response with automatic refinement on failure.

        Returns
        -------
        tuple[Dict[str, Any], bool]
            (parsed_data, parse_error_flag)
            - If successful: (data, False)
            - If failed after refinement: (empty_data_with_error_summary, True)
        """
        cleaned = self._clean_json_response(raw)

        # First attempt: parse directly
        data, error = self._try_parse_judge_json(cleaned)
        if data is not None:
            return data, False

        logger.warning("[%s] Failed to parse Judge JSON: %s", file_name, error)
        logger.info("[%s] Calling Refiner agent to repair JSON …", file_name)

        # Call Refiner agent
        try:
            refiner_response = self._llm.chat(
                messages=[
                    {"role": "system", "content": REFINER_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": REFINER_USER_TEMPLATE.format(
                            malformed_json=cleaned,
                            error_message=error,
                        ),
                    },
                ]
            )
        except RuntimeError as exc:
            logger.error("[%s] Refiner LLM call failed: %s", file_name, exc)
            return {
                "verified_violations": [],
                "analysis_summary": f"JSON parse error: {error}. Refiner call failed.",
            }, True

        # Second attempt: parse refined JSON
        refined_cleaned = self._clean_json_response(refiner_response)
        data, second_error = self._try_parse_judge_json(refined_cleaned)
        if data is not None:
            logger.info("[%s] Refiner successfully repaired JSON.", file_name)
            return data, False

        # Both attempts failed
        logger.error(
            "[%s] Refiner could not repair JSON. Original error: %s | Refiner error: %s",
            file_name,
            error,
            second_error,
        )
        return {
            "verified_violations": [],
            "analysis_summary": f"JSON parse error: {error}. Refiner failed: {second_error}",
        }, True

    # ------------------------------------------------------------------
    # RAG helpers
    # ------------------------------------------------------------------
    def _fetch_rag_context(self, queries: List[str]) -> List[str]:
        if self._rag is None:
            return []
        seen: set[str] = set()
        chunks: List[str] = []
        for q in queries:
            for chunk in self._rag.retrieve(q):
                if chunk not in seen:
                    seen.add(chunk)
                    chunks.append(chunk)
        return chunks

    @staticmethod
    def _error_result(file_path: str, message: str) -> Dict[str, Any]:
        return {
            "file": file_path,
            "language": "unknown",
            "score": 0,
            "violations": [],
            "summary": message,
            "reliability_analysis": message,
            "maintainability_analysis": "",
            "error": message,
        }
