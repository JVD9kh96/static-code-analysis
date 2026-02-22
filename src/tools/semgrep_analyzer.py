"""
Shared Semgrep wrapper – language-agnostic pattern-based analysis.

Semgrep runs community (``--config auto``) or user-specified rules against any
supported language.  It returns SARIF-style JSON that we normalise into a
flat list of findings.
"""

from __future__ import annotations

import json
import logging
import subprocess
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def run_semgrep(file_path: str, *, config: str = "auto") -> Dict[str, Any]:
    """
    Run Semgrep on *file_path* and return structured findings.

    Parameters
    ----------
    file_path : str
        Path to a single source file.
    config : str
        Semgrep configuration specifier.  ``"auto"`` uses the community
        rulesets (requires network on first run; results are cached).
        Can also be a local YAML path or a registry entry like
        ``"p/python"`` / ``"p/csharp"``.

    Returns
    -------
    dict
        ``{"findings": [{"rule_id", "severity", "message", "line",
        "end_line", "category"}], "error": str | None}``
    """
    result: Dict[str, Any] = {"findings": [], "error": None}
    try:
        proc = subprocess.run(
            [
                "semgrep", "scan",
                "--json",
                "--quiet",
                "--config", config,
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw = (proc.stdout or "").strip()
        if not raw:
            if proc.returncode != 0 and proc.stderr:
                err_hint = proc.stderr.strip().splitlines()[-1][:200]
                result["error"] = f"Semgrep exited {proc.returncode}: {err_hint}"
            return result

        data = json.loads(raw)
        for r in data.get("results", []):
            extra = r.get("extra", {})
            metadata = extra.get("metadata", {})
            result["findings"].append({
                "rule_id": r.get("check_id", ""),
                "severity": extra.get("severity", "WARNING").upper(),
                "message": extra.get("message", ""),
                "line": r.get("start", {}).get("line", 0),
                "end_line": r.get("end", {}).get("line", 0),
                "category": metadata.get("category", ""),
            })
    except FileNotFoundError:
        result["error"] = (
            "'semgrep' CLI not found. "
            "Install via: pip install semgrep  (or pipx install semgrep)"
        )
    except subprocess.TimeoutExpired:
        result["error"] = "Semgrep timed out."
    except (json.JSONDecodeError, KeyError) as exc:
        result["error"] = f"Failed to parse Semgrep output: {exc}"
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"Semgrep execution error: {exc}"
    return result


def format_semgrep_summary(semgrep_result: Dict[str, Any]) -> str:
    """
    Format Semgrep findings into a human-readable summary for LLM prompts.
    """
    findings = semgrep_result.get("findings", [])
    if findings:
        lines: List[str] = []
        for f in findings[:30]:
            rule_short = f["rule_id"].rsplit(".", 1)[-1] if f["rule_id"] else "?"
            lines.append(
                f"  L{f['line']}: [{f['severity']}] {rule_short} – {f['message']}"
            )
        return "\n".join(lines)
    if semgrep_result.get("error"):
        return f"  Error: {semgrep_result['error']}"
    return "  No Semgrep findings."
