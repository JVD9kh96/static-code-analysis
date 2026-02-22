"""
C# language profile – wires .NET-specific tools, prompts, and scoring.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from src.languages.base import LanguageProfile
from src.tools.csharp_analyzer import CSharpTools
from src.agent.prompts import (
    CS_DETECTIVE_SYSTEM_PROMPT,
    CS_DETECTIVE_USER_TEMPLATE,
    CS_JUDGE_SYSTEM_PROMPT,
    CS_JUDGE_USER_TEMPLATE,
)

_IMPORT_TOPIC_MAP: Dict[str, str] = {
    "System.Data": "database rules",
    "SqlClient": "database rules",
    "EntityFramework": "database rules",
    "Microsoft.EntityFrameworkCore": "database rules",
    "System.Diagnostics.Process": "security subprocess rules",
    "Process.Start": "security subprocess rules",
    "Assembly.Load": "security eval rules",
    "Activator.CreateInstance": "security eval rules",
    "Console.Write": "logging rules",
    "ILogger": "logging rules",
    "Serilog": "logging rules",
    "NLog": "logging rules",
    "System.Random": "security random token rules",
    "RandomNumberGenerator": "security random token rules",
    "System.Threading": "concurrency rules",
    "Task.Run": "concurrency rules",
    "Parallel.": "concurrency rules",
    "HttpClient": "error handling rules",
    "WebClient": "error handling rules",
    "Xunit": "testing rules",
    "NUnit": "testing rules",
    "MSTest": "testing rules",
    "Newtonsoft.Json": "serialization rules",
    "System.Text.Json": "serialization rules",
    "BinaryFormatter": "security deserialization rules",
}

_PENALTY_CRITICAL = 15
_PENALTY_MAJOR = 7
_PENALTY_MINOR = 2
_PENALTY_COMPLEXITY = 5
_COMPLEXITY_THRESHOLD = 15


class CSharpProfile(LanguageProfile):
    """Full evaluation profile for C# source files."""

    _tools = CSharpTools()

    # ── metadata ──────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return "C#"

    @property
    def extensions(self) -> Set[str]:
        return {".cs"}

    # ── tools ─────────────────────────────────────────────────────────
    def run_tools(self, file_path: str) -> Dict[str, Any]:
        return self._tools.run_all(file_path)

    def filter_lint(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        return CSharpTools.filter_build_diagnostics(tools.get("dotnet_build", {}))

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
        return CS_DETECTIVE_SYSTEM_PROMPT

    @property
    def judge_system_prompt(self) -> str:
        return CS_JUDGE_SYSTEM_PROMPT

    def build_detective_user(
        self,
        file_path: str,
        source_code: str,
        tools: Dict[str, Any],
        rag_chunks: List[str],
    ) -> str:
        devskim = tools.get("devskim", {"issues": [], "error": None})
        issues = devskim.get("issues", [])
        if issues:
            devskim_summary = "\n".join(
                f"  L{i['line_number']}: [{i['severity']}] "
                f"{i['rule_id']} – {i['description']}"
                for i in issues
            )
        else:
            devskim_summary = (
                "  No security issues."
                if not devskim.get("error")
                else f"  Error: {devskim['error']}"
            )

        rag_context = (
            "\n\n".join(rag_chunks)
            if rag_chunks
            else "(RAG disabled – no company guidelines provided.)"
        )

        return CS_DETECTIVE_USER_TEMPLATE.format(
            file_path=file_path,
            source_code=source_code,
            devskim_summary=devskim_summary,
            rag_context=rag_context,
        )

    def build_judge_user(
        self,
        file_path: str,
        source_code: str,
        potential_issues: List[Dict[str, Any]],
        tools: Dict[str, Any],
    ) -> str:
        filtered_build = self.filter_lint(tools)

        issues_text = (
            json.dumps(potential_issues, indent=2)
            if potential_issues
            else "[]  (Detective found no potential issues.)"
        )

        diags = filtered_build.get("diagnostics", [])
        if diags:
            build_summary = "\n".join(
                f"  L{d['line']}: [{d['severity']}] {d['id']} – {d['message']}"
                for d in diags[:25]
            )
        else:
            build_summary = (
                "  No build diagnostics."
                if not filtered_build.get("error")
                else f"  Error: {filtered_build['error']}"
            )

        return CS_JUDGE_USER_TEMPLATE.format(
            file_path=file_path,
            source_code=source_code,
            potential_issues=issues_text,
            build_summary=build_summary,
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

        complexity = tools.get("complexity", {})
        for b in complexity.get("blocks", []):
            if b.get("complexity", 0) > _COMPLEXITY_THRESHOLD:
                score -= _PENALTY_COMPLEXITY
                break

        return max(0, min(100, score))
