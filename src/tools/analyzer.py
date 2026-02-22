"""
Deterministic static-analysis wrappers for Pylint, Radon, and Bandit.

Each method accepts a file path and returns structured dictionaries –
never raw stdout strings.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StaticTools:
    """Facade over Pylint, Radon, and Bandit CLI tools."""

    # ------------------------------------------------------------------
    # Pylint
    # ------------------------------------------------------------------
    @staticmethod
    def run_pylint(file_path: str) -> Dict[str, Any]:
        """
        Run Pylint on *file_path* and return a structured report.

        Returns
        -------
        dict
            ``{"score": float, "messages": [{"type", "module", "line",
            "column", "message", "symbol"}], "error": str | None}``
        """
        result: Dict[str, Any] = {"score": 0.0, "messages": [], "error": None}
        try:
            proc = subprocess.run(
                [
                    sys.executable, "-m", "pylint",
                    "--output-format=json2",
                    "--disable=C0114,C0115,C0116",  # skip missing-docstring noise
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            # Pylint exits non-zero when it finds issues – that is expected.
            if proc.stdout.strip():
                payload = json.loads(proc.stdout)
                messages = payload.get("messages", [])
                result["messages"] = [
                    {
                        # pylint json2 commonly uses type like: convention|refactor|warning|error|fatal
                        "type": m.get("type", ""),
                        # keep message-id when available (e.g., C0301, W0511)
                        "message_id": (
                            m.get("messageId")
                            or m.get("message-id")
                            or m.get("message_id")
                            or ""
                        ),
                        "module": m.get("module", ""),
                        "line": m.get("line", 0),
                        "column": m.get("column", 0),
                        "message": m.get("message", ""),
                        "symbol": m.get("symbol", ""),
                    }
                    for m in messages
                ]
                # Extract score from statistics if available
                stats = payload.get("statistics", {})
                result["score"] = stats.get("score", 0.0)

        except subprocess.TimeoutExpired:
            result["error"] = "Pylint timed out."
        except (json.JSONDecodeError, KeyError) as exc:
            result["error"] = f"Failed to parse Pylint output: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"Pylint execution error: {exc}"
        return result

    # ------------------------------------------------------------------
    # Radon – Cyclomatic Complexity
    # ------------------------------------------------------------------
    @staticmethod
    def run_radon(file_path: str) -> Dict[str, Any]:
        """
        Run ``radon cc`` on *file_path* and return complexity metrics.

        Returns
        -------
        dict
            ``{"blocks": [{"name", "type", "complexity", "rank",
            "lineno"}], "average_complexity": float, "error": str | None}``
        """
        result: Dict[str, Any] = {
            "blocks": [],
            "average_complexity": 0.0,
            "error": None,
        }
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "radon", "cc", "-j", "-a", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.stdout.strip():
                data = json.loads(proc.stdout)
                # radon JSON output: {"filepath": [blocks...]}
                for _path, blocks in data.items():
                    if isinstance(blocks, list):
                        for b in blocks:
                            result["blocks"].append(
                                {
                                    "name": b.get("name", ""),
                                    "type": b.get("type", ""),
                                    "complexity": b.get("complexity", 0),
                                    "rank": b.get("rank", "?"),
                                    "lineno": b.get("lineno", 0),
                                }
                            )
                if result["blocks"]:
                    total = sum(b["complexity"] for b in result["blocks"])
                    result["average_complexity"] = round(
                        total / len(result["blocks"]), 2
                    )
        except subprocess.TimeoutExpired:
            result["error"] = "Radon timed out."
        except (json.JSONDecodeError, KeyError) as exc:
            result["error"] = f"Failed to parse Radon output: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"Radon execution error: {exc}"
        return result

    # ------------------------------------------------------------------
    # Bandit – Security Linting
    # ------------------------------------------------------------------
    @staticmethod
    def run_bandit(file_path: str) -> Dict[str, Any]:
        """
        Run Bandit on *file_path* and return security findings.

        Returns
        -------
        dict
            ``{"issues": [{"severity", "confidence", "test_id",
            "test_name", "line_number", "issue_text"}],
            "metrics": dict, "error": str | None}``
        """
        result: Dict[str, Any] = {"issues": [], "metrics": {}, "error": None}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "bandit", "-f", "json", "-q", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            raw = proc.stdout.strip()
            if raw:
                data = json.loads(raw)
                for issue in data.get("results", []):
                    result["issues"].append(
                        {
                            "severity": issue.get("issue_severity", ""),
                            "confidence": issue.get("issue_confidence", ""),
                            "test_id": issue.get("test_id", ""),
                            "test_name": issue.get("test_name", ""),
                            "line_number": issue.get("line_number", 0),
                            "issue_text": issue.get("issue_text", ""),
                        }
                    )
                result["metrics"] = data.get("metrics", {})
        except subprocess.TimeoutExpired:
            result["error"] = "Bandit timed out."
        except (json.JSONDecodeError, KeyError) as exc:
            result["error"] = f"Failed to parse Bandit output: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"Bandit execution error: {exc}"
        return result

    # ------------------------------------------------------------------
    # Pylint Filtering – reduce noise for the Judge agent
    # ------------------------------------------------------------------
    @staticmethod
    def filter_pylint_results(
        raw_result: Dict[str, Any],
        low_score_threshold: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Filter Pylint messages to reduce noise for the Judge agent.

        Strategy:
        - Always drop specific known-noise message IDs (even if warnings).
        - If score is very low (< low_score_threshold), keep more signals.
        - Otherwise, keep mainly errors/warnings/fatal; drop convention/refactor.

        Returns the same structure as run_pylint but with filtered messages.
        """
        out = {k: v for k, v in raw_result.items()}
        messages = list(raw_result.get("messages", []) or [])
        score = raw_result.get("score", 0.0)

        # Pylint IDs to always ignore (token-wasters / low-value noise)
        IGNORED_MESSAGE_IDS = {
            "C0114", "C0115", "C0116",  # missing docstrings
            "C0301",  # line-too-long
            "W0511",  # fixme / todo
            "R0903",  # too-few-public-methods
            "R0913",  # too-many-arguments
        }

        def _type_bucket(m: Dict[str, Any]) -> str:
            t = (m.get("type") or "").strip().lower()
            # json2 uses full words; some tooling may provide single letters
            if t in {"fatal", "f"}:
                return "fatal"
            if t in {"error", "e"}:
                return "error"
            if t in {"warning", "w"}:
                return "warning"
            if t in {"convention", "c"}:
                return "convention"
            if t in {"refactor", "r"}:
                return "refactor"
            return t or "unknown"

        filtered: List[Dict[str, Any]] = []
        for m in messages:
            msg_id = (m.get("message_id") or "").strip()
            if msg_id in IGNORED_MESSAGE_IDS:
                continue

            bucket = _type_bucket(m)

            # Always keep high-signal buckets
            if bucket in {"fatal", "error", "warning"}:
                filtered.append(m)
                continue

            # Keep convention/refactor only if score is very low
            if bucket in {"convention", "refactor"}:
                if isinstance(score, (int, float)) and score < low_score_threshold:
                    filtered.append(m)
                continue

            # Unknown buckets: keep only when score is very low
            if isinstance(score, (int, float)) and score < low_score_threshold:
                filtered.append(m)

        out["messages"] = filtered
        return out

    # ------------------------------------------------------------------
    # MyPy – deterministic type checking (optional dependency)
    # ------------------------------------------------------------------
    @staticmethod
    def run_mypy(file_path: str) -> Dict[str, Any]:
        """
        Run MyPy on *file_path* and return structured type errors.

        Returns
        -------
        dict
            ``{\"errors\": [{\"line\", \"message\", \"code\"}], \"error\": str | None}``
        """
        result: Dict[str, Any] = {"errors": [], "error": None}
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--no-error-summary",
                    "--show-error-codes",
                    "--pretty",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            # mypy exits non-zero when it finds issues – that is expected.
            output = (proc.stdout or "").strip()
            if not output:
                return result

            # Typical line format:
            # path/to/file.py:12: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
            pattern = re.compile(
                r"^(?P<file>.+?):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<level>error|note):\s*(?P<msg>.+?)(?:\s*\[(?P<code>[a-zA-Z0-9_-]+)\])?\s*$"
            )
            for line in output.splitlines():
                m = pattern.match(line.strip())
                if not m:
                    continue
                if m.group("level") != "error":
                    continue
                result["errors"].append(
                    {
                        "line": int(m.group("line")),
                        "message": m.group("msg"),
                        "code": m.group("code") or "",
                    }
                )
        except subprocess.TimeoutExpired:
            result["error"] = "MyPy timed out."
        except Exception as exc:  # noqa: BLE001
            # If mypy isn't installed, this will commonly surface as a module error.
            result["error"] = f"MyPy execution error: {exc}"
        return result

    # ------------------------------------------------------------------
    # Convenience – run all three
    # ------------------------------------------------------------------
    def run_all(self, file_path: str) -> Dict[str, Any]:
        """Run Pylint, Radon, and Bandit and merge results."""
        return {
            "pylint": self.run_pylint(file_path),
            "radon": self.run_radon(file_path),
            "bandit": self.run_bandit(file_path),
            "mypy": self.run_mypy(file_path),
        }
