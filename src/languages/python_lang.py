"""
Python language profile – wires Python-specific tools, prompts, and scoring.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from src.languages.base import LanguageProfile
from src.tools.analyzer import StaticTools
from src.agent.prompts import (
    DETECTIVE_SYSTEM_PROMPT as PY_DET_SYS,
    DETECTIVE_USER_TEMPLATE as PY_DET_USR,
    JUDGE_SYSTEM_PROMPT as PY_JUDGE_SYS,
    JUDGE_USER_TEMPLATE as PY_JUDGE_USR,
)

_IMPORT_TOPIC_MAP: Dict[str, str] = {
    "sqlalchemy": "database rules",
    "sqlite3": "database rules",
    "psycopg": "database rules",
    "pymongo": "database rules",
    "subprocess": "security subprocess rules",
    "os.system": "security subprocess rules",
    "eval": "security eval rules",
    "exec": "security eval rules",
    "print": "logging rules",
    "logging": "logging rules",
    "random": "security random token rules",
    "secrets": "security random token rules",
    "threading": "concurrency rules",
    "concurrent": "concurrency rules",
    "pytest": "testing rules",
    "unittest": "testing rules",
    "requests": "error handling rules",
    "flask": "error handling rules",
    "fastapi": "error handling rules",
}

_PENALTY_CRITICAL = 15
_PENALTY_MAJOR = 7
_PENALTY_MINOR = 2
_PENALTY_COMPLEXITY = 5
_COMPLEXITY_THRESHOLD = 15


class PythonProfile(LanguageProfile):
    """Full evaluation profile for Python source files."""

    _tools = StaticTools()

    # ── metadata ──────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return "Python"

    @property
    def extensions(self) -> Set[str]:
        return {".py"}

    # ── tools ─────────────────────────────────────────────────────────
    def run_tools(self, file_path: str) -> Dict[str, Any]:
        return self._tools.run_all(file_path)

    def filter_lint(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        return StaticTools.filter_pylint_results(tools["pylint"])

    # ── RAG ────────────────────────────────────────────────────────────
    def derive_rag_queries(self, source_code: str) -> List[str]:
        queries: List[str] = []
        seen: set[str] = set()
        for keyword, topic in _IMPORT_TOPIC_MAP.items():
            if keyword in source_code and topic not in seen:
                queries.append(topic)
                seen.add(topic)
        if "general code style" not in seen:
            queries.append("general code style")
        return queries

    # ── prompts ────────────────────────────────────────────────────────
    @property
    def detective_system_prompt(self) -> str:
        return PY_DET_SYS

    @property
    def judge_system_prompt(self) -> str:
        return PY_JUDGE_SYS

    def build_detective_user(
        self,
        file_path: str,
        source_code: str,
        tools: Dict[str, Any],
        rag_chunks: List[str],
    ) -> str:
        bandit = tools["bandit"]
        bandit_issues = bandit.get("issues", [])
        if bandit_issues:
            bandit_summary = "\n".join(
                f"  L{i['line_number']}: [{i['severity']}/{i['confidence']}] "
                f"{i['test_id']} {i['test_name']} – {i['issue_text']}"
                for i in bandit_issues
            )
        else:
            bandit_summary = (
                "  No security issues."
                if not bandit.get("error")
                else f"  Error: {bandit['error']}"
            )

        rag_context = (
            "\n\n".join(rag_chunks)
            if rag_chunks
            else "(RAG disabled – no company guidelines provided.)"
        )

        return PY_DET_USR.format(
            file_path=file_path,
            source_code=source_code,
            bandit_summary=bandit_summary,
            rag_context=rag_context,
        )

    def build_judge_user(
        self,
        file_path: str,
        source_code: str,
        potential_issues: List[Dict[str, Any]],
        tools: Dict[str, Any],
    ) -> str:
        filtered_pylint = self.filter_lint(tools)
        mypy = tools.get("mypy", {"errors": [], "error": None})

        issues_text = (
            json.dumps(potential_issues, indent=2)
            if potential_issues
            else "[]  (Detective found no potential issues.)"
        )

        pylint_msgs = filtered_pylint.get("messages", [])
        if pylint_msgs:
            pylint_summary = "\n".join(
                f"  L{m['line']}: [{m['type']}] {m['symbol']} – {m['message']}"
                for m in pylint_msgs[:25]
            )
        else:
            pylint_summary = (
                "  No Pylint issues."
                if not filtered_pylint.get("error")
                else f"  Error: {filtered_pylint['error']}"
            )

        mypy_errors = mypy.get("errors", []) if isinstance(mypy, dict) else []
        if mypy.get("error"):
            mypy_summary = f"  Error: {mypy['error']}"
        elif mypy_errors:
            mypy_summary = "\n".join(
                f"  L{e.get('line', '?')}: {e.get('message', '')} [{e.get('code', '')}]".rstrip()
                for e in mypy_errors[:25]
            )
        else:
            mypy_summary = "  No MyPy type errors."

        return PY_JUDGE_USR.format(
            file_path=file_path,
            source_code=source_code,
            potential_issues=issues_text,
            pylint_summary=pylint_summary,
            mypy_summary=mypy_summary,
        )

    # ── scoring ────────────────────────────────────────────────────────
    def calculate_score(
        self,
        verified_violations: List[Dict[str, Any]],
        tools: Dict[str, Any],
    ) -> int:
        score = 100
        for v in verified_violations:
            sev = (v.get("severity") or "").strip().capitalize()
            if sev == "Critical":
                score -= _PENALTY_CRITICAL
            elif sev == "Major":
                score -= _PENALTY_MAJOR
            elif sev == "Minor":
                score -= _PENALTY_MINOR

        radon = tools.get("radon", {})
        for b in radon.get("blocks", []):
            if b.get("complexity", 0) > _COMPLEXITY_THRESHOLD:
                score -= _PENALTY_COMPLEXITY
                break

        return max(0, min(100, score))
