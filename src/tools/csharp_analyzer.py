"""
Deterministic static-analysis wrappers for C# code.

Tools:
- ``dotnet build``   – compiler diagnostics (errors, warnings, type checks)
- ``DevSkim``        – security linting (SARIF JSON output)
- Simple regex-based cyclomatic complexity counter
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CSharpTools:
    """Facade over C# static analysis tools."""

    # ------------------------------------------------------------------
    # dotnet build – compiler diagnostics
    # ------------------------------------------------------------------
    @staticmethod
    def run_dotnet_build(file_path: str) -> Dict[str, Any]:
        """
        Attempt to compile the C# file and capture diagnostics.

        Looks for the nearest ``.csproj`` up the directory tree so that
        ``dotnet build`` has a project context.  When no project file is
        found, returns an informational error but does **not** crash.
        """
        result: Dict[str, Any] = {"diagnostics": [], "error": None}
        src = Path(file_path).resolve()

        csproj = CSharpTools._find_nearest(src.parent, "*.csproj")
        if csproj is None:
            result["error"] = (
                "No .csproj found; dotnet build diagnostics unavailable. "
                "Place a .csproj in a parent directory to enable compilation checks."
            )
            return result

        try:
            proc = subprocess.run(
                [
                    "dotnet", "build",
                    str(csproj),
                    "--no-restore",
                    "-consoleloggerparameters:NoSummary",
                    "-verbosity:quiet",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            pattern = re.compile(
                r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\)\s*:\s*"
                r"(?P<level>error|warning)\s+(?P<id>\w+)\s*:\s*(?P<msg>.+)$",
                re.MULTILINE,
            )
            for m in pattern.finditer(output):
                diag_file = Path(m.group("file")).resolve()
                if diag_file != src:
                    continue
                result["diagnostics"].append({
                    "id": m.group("id"),
                    "severity": m.group("level"),
                    "message": m.group("msg").strip(),
                    "line": int(m.group("line")),
                    "column": int(m.group("col")),
                })
        except FileNotFoundError:
            result["error"] = (
                "'dotnet' CLI not found. Install the .NET SDK to enable build diagnostics."
            )
        except subprocess.TimeoutExpired:
            result["error"] = "dotnet build timed out."
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"dotnet build error: {exc}"
        return result

    # ------------------------------------------------------------------
    # DevSkim – security linting
    # ------------------------------------------------------------------
    @staticmethod
    def run_devskim(file_path: str) -> Dict[str, Any]:
        """
        Run DevSkim on *file_path* and return security findings.

        DevSkim outputs SARIF (JSON). We extract rule-id, severity,
        description, and line number from the SARIF results.
        """
        result: Dict[str, Any] = {"issues": [], "error": None}
        try:
            proc = subprocess.run(
                [
                    "devskim", "analyze",
                    "--source-code", str(file_path),
                    "-f", "sarif",
                    "-o", "-",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            raw = (proc.stdout or "").strip()
            if not raw:
                return result
            sarif = json.loads(raw)
            for run in sarif.get("runs", []):
                for r in run.get("results", []):
                    loc = (r.get("locations") or [{}])[0]
                    region = loc.get("physicalLocation", {}).get("region", {})
                    result["issues"].append({
                        "rule_id": r.get("ruleId", ""),
                        "severity": r.get("level", "warning"),
                        "description": (r.get("message", {}).get("text", "")),
                        "line_number": region.get("startLine", 0),
                    })
        except FileNotFoundError:
            result["error"] = (
                "'devskim' CLI not found. "
                "Install via: dotnet tool install -g Microsoft.CST.DevSkim.CLI"
            )
        except subprocess.TimeoutExpired:
            result["error"] = "DevSkim timed out."
        except (json.JSONDecodeError, KeyError) as exc:
            result["error"] = f"Failed to parse DevSkim output: {exc}"
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"DevSkim execution error: {exc}"
        return result

    # ------------------------------------------------------------------
    # Simple cyclomatic complexity (regex-based)
    # ------------------------------------------------------------------
    @staticmethod
    def run_complexity(file_path: str) -> Dict[str, Any]:
        """
        Estimate cyclomatic complexity for each method in a C# file.

        Uses a simple regex heuristic: count branching keywords
        (``if``, ``else if``, ``case``, ``for``, ``foreach``, ``while``,
        ``do``, ``catch``, ``&&``, ``||``, ``??``) within each method body.
        """
        result: Dict[str, Any] = {
            "blocks": [],
            "average_complexity": 0.0,
            "error": None,
        }
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            result["error"] = f"Cannot read file: {exc}"
            return result

        method_pattern = re.compile(
            r"(?:public|private|protected|internal|static|virtual|override|async|abstract|sealed|\s)*"
            r"\s+\w[\w<>\[\],\s]*?\s+(?P<name>\w+)\s*\([^)]*\)\s*(?:\{)",
            re.MULTILINE,
        )
        branch_pattern = re.compile(
            r"\b(?:if|else\s+if|case|for|foreach|while|do|catch)\b|&&|\|\||\?\?"
        )

        for m in method_pattern.finditer(source):
            name = m.group("name")
            start = m.end()
            body = CSharpTools._extract_brace_block(source, start - 1)
            cc = 1 + len(branch_pattern.findall(body))
            lineno = source[:m.start()].count("\n") + 1
            rank = "A" if cc <= 5 else "B" if cc <= 10 else "C" if cc <= 20 else "D"
            result["blocks"].append({
                "name": name,
                "type": "method",
                "complexity": cc,
                "rank": rank,
                "lineno": lineno,
            })

        if result["blocks"]:
            total = sum(b["complexity"] for b in result["blocks"])
            result["average_complexity"] = round(total / len(result["blocks"]), 2)
        return result

    # ------------------------------------------------------------------
    # Filter build diagnostics (remove low-value noise)
    # ------------------------------------------------------------------
    @staticmethod
    def filter_build_diagnostics(
        raw: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Filter ``dotnet build`` diagnostics to keep only high-signal items.

        Drops:
        - CS1591 (missing XML comment)
        - CS8618 (nullable reference uninitialized in constructor) when
          clearly a DTO / simple class.
        """
        IGNORED_IDS = {"CS1591"}
        out = dict(raw)
        diags = list(raw.get("diagnostics", []))
        out["diagnostics"] = [
            d for d in diags if d.get("id", "") not in IGNORED_IDS
        ]
        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _find_nearest(start: Path, glob: str) -> Optional[Path]:
        """Walk up the directory tree to find the first file matching *glob*."""
        current = start
        for _ in range(20):
            matches = list(current.glob(glob))
            if matches:
                return matches[0]
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    @staticmethod
    def _extract_brace_block(source: str, open_pos: int) -> str:
        """Extract text inside a brace-delimited block starting at *open_pos*."""
        depth = 0
        i = open_pos
        while i < len(source):
            ch = source[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[open_pos + 1 : i]
            i += 1
        return source[open_pos + 1 :]

    # ------------------------------------------------------------------
    # Convenience – run all
    # ------------------------------------------------------------------
    def run_all(self, file_path: str) -> Dict[str, Any]:
        return {
            "dotnet_build": self.run_dotnet_build(file_path),
            "devskim": self.run_devskim(file_path),
            "complexity": self.run_complexity(file_path),
        }
