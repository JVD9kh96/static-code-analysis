#!/usr/bin/env python3
"""
Agentic Static Code Evaluator – CLI entry point.

Usage
-----
    python -m src.main <directory>                    # scan a directory (auto-detect language)
    python -m src.main <file.py>                      # scan a single Python file
    python -m src.main <file.cs>                      # scan a single C# file
    python -m src.main <directory> --lang python      # force Python-only scan
    python -m src.main <directory> --lang csharp      # force C#-only scan
    python -m src.main <directory> -w 8               # use 8 worker threads
    python -m src.main <directory> --no-rag            # skip RAG entirely
    python -m src.main <directory> -o report.json      # save results as JSON
    python -m src.main <directory> -o report.csv       # save results as CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table
from rich.text import Text

from src.agent.evaluator import Evaluator
from src.agent.llm_client import LLMClient
from src.languages import SUPPORTED_EXTENSIONS, get_profile
from src.utils.config import settings

console = Console()


# ------------------------------------------------------------------
# CLI argument parser
# ------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-eval",
        description="Agentic Static Code Evaluator – hybrid deterministic + LLM analysis.",
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to a source file or directory to evaluate.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        choices=["python", "csharp", "auto"],
        help=(
            "Language to evaluate (default: auto-detect from file extensions). "
            "Use 'python' or 'csharp' to restrict to one language."
        ),
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=settings.max_workers,
        help=f"Number of parallel worker threads (default: {settings.max_workers}).",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Skip the RAG knowledge-base ingestion step.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help=(
            "Save results to a file. Supports .json and .csv extensions "
            "(e.g. -o report.json or -o report.csv)."
        ),
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser


# ------------------------------------------------------------------
# File discovery
# ------------------------------------------------------------------
def _discover_files(target: str, lang: str | None = None) -> List[Path]:
    """
    Discover source files to evaluate.

    Parameters
    ----------
    target : str
        File or directory path.
    lang : str | None
        ``None`` or ``"auto"`` → scan all supported extensions.
        ``"python"`` → only ``.py``.
        ``"csharp"`` → only ``.cs``.
    """
    p = Path(target)

    if lang and lang != "auto":
        profile = get_profile(lang)
        exts = profile.extensions
    else:
        exts = SUPPORTED_EXTENSIONS

    if p.is_file():
        if p.suffix.lower() in exts:
            return [p]
        console.print(
            f"[red]Error:[/red] {target} has extension '{p.suffix}' which "
            f"is not in the supported set {exts}."
        )
        sys.exit(1)

    if p.is_dir():
        files: List[Path] = []
        for ext in sorted(exts):
            files.extend(p.rglob(f"*{ext}"))
        return sorted(set(files))

    console.print(f"[red]Error:[/red] {target} is not a valid file or directory.")
    sys.exit(1)


# ------------------------------------------------------------------
# Directory tree display
# ------------------------------------------------------------------
def _build_tree(root: Path, files: List[Path]) -> Dict[str, Any]:
    """
    Build a nested dictionary representing the directory tree.
    Only includes directories that contain discovered files.
    """
    tree: Dict[str, Any] = {"__files__": []}
    
    for file_path in files:
        try:
            rel_path = file_path.relative_to(root)
        except ValueError:
            rel_path = file_path
        
        parts = rel_path.parts
        current = tree
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {"__files__": []}
            current = current[part]
        
        current["__files__"].append(parts[-1])
    
    return tree


def _print_tree(
    tree: Dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    is_root: bool = True,
    root_name: str = "",
) -> None:
    """Recursively print the directory tree with box-drawing characters."""
    if is_root:
        console.print(f"[bold blue]📁 {root_name}/[/bold blue]")
        prefix = ""
    
    dirs = sorted(k for k in tree.keys() if k != "__files__")
    files = sorted(tree.get("__files__", []))
    
    items = [(d, True) for d in dirs] + [(f, False) for f in files]
    
    for i, (name, is_dir) in enumerate(items):
        is_last_item = i == len(items) - 1
        connector = "└── " if is_last_item else "├── "
        
        if is_dir:
            console.print(f"{prefix}{connector}[bold blue]📁 {name}/[/bold blue]")
            extension = "    " if is_last_item else "│   "
            _print_tree(
                tree[name],
                prefix=prefix + extension,
                is_last=is_last_item,
                is_root=False,
            )
        else:
            ext = Path(name).suffix.lower()
            icon = "🐍" if ext == ".py" else "🔷" if ext == ".cs" else "📄"
            console.print(f"{prefix}{connector}{icon} {name}")


def _display_project_structure(target: Path, files: List[Path]) -> None:
    """Display the project structure as a tree before analysis."""
    if not files:
        return
    
    if target.is_file():
        ext = target.suffix.lower()
        icon = "🐍" if ext == ".py" else "🔷" if ext == ".cs" else "📄"
        console.print(f"\n{icon} [bold]{target.name}[/bold]\n")
        return
    
    console.print("\n[bold cyan]Project Structure[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")
    
    tree = _build_tree(target, files)
    _print_tree(tree, root_name=target.name)
    
    console.print("[dim]─" * 40 + "[/dim]")


# ------------------------------------------------------------------
# Pretty-print helpers
# ------------------------------------------------------------------
def _is_score_na(score: Any) -> bool:
    """Check if score is N/A (parse error occurred)."""
    return score == "N/A" or score == "n/a"


def _score_color(score: Any) -> str:
    """Return color based on score value. Handles N/A scores."""
    if _is_score_na(score):
        return "magenta"
    if not isinstance(score, (int, float)):
        return "red"
    if score >= 90:
        return "green"
    if score >= 70:
        return "yellow"
    if score >= 50:
        return "dark_orange"
    return "red"


def _print_summary_table(results: List[Dict[str, Any]]) -> None:
    table = Table(
        title="Evaluation Summary",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("File", style="bold")
    table.add_column("Lang", width=8)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Violations", justify="center", width=11)
    table.add_column("Verdict", min_width=20)

    for idx, r in enumerate(results, 1):
        score = r.get("score", 0)
        color = _score_color(score)
        n_violations = len(r.get("violations", []))
        verdict = (r.get("summary") or r.get("reliability_analysis", ""))[:80]
        
        if r.get("parse_error"):
            verdict = f"[magenta]Parse error – see summary[/magenta]"
        elif r.get("error"):
            verdict = f"[red]{r['error']}[/red]"

        score_display = str(score) if not _is_score_na(score) else "[magenta]N/A[/magenta]"

        table.add_row(
            str(idx),
            str(Path(r.get("file", "?")).name),
            r.get("language", "?"),
            f"[{color}]{score_display}[/{color}]" if not _is_score_na(score) else score_display,
            str(n_violations),
            verdict,
        )

    console.print()
    console.print(table)


def _print_detail(result: Dict[str, Any]) -> None:
    score = result.get("score", 0)
    color = _score_color(score)
    file_name = Path(result.get("file", "?")).name
    lang = result.get("language", "?")

    if _is_score_na(score):
        header = Text.assemble(
            (f" {file_name} ", "bold white on blue"),
            (f" [{lang}] ", "dim"),
            ("  Score: ", ""),
            ("N/A", "bold magenta"),
            (" (parse error)", "dim magenta"),
        )
    else:
        header = Text.assemble(
            (f" {file_name} ", "bold white on blue"),
            (f" [{lang}] ", "dim"),
            ("  Score: ", ""),
            (str(score), f"bold {color}"),
            ("/100", "dim"),
        )
    console.print(Panel(header, expand=False))
    
    if result.get("parse_error"):
        console.print(f"  [magenta bold]⚠ Parse Error:[/magenta bold] Judge JSON could not be parsed. Refiner attempted repair.")
        summary = result.get("summary", "")
        if summary:
            console.print(f"  [dim]{summary}[/dim]")

    summary = result.get("summary") or result.get("reliability_analysis")
    if summary:
        console.print(f"  [bold]Summary:[/bold]  {summary}")

    violations = result.get("violations", [])
    if violations:
        vt = Table(show_header=True, header_style="bold magenta", box=None, pad_edge=False)
        vt.add_column("Line", justify="right", width=6)
        vt.add_column("Severity", width=10)
        vt.add_column("Message")
        vt.add_column("Proof")
        vt.add_column("Reasoning")
        vt.add_column("Fix")
        for v in violations:
            vt.add_row(
                str(v.get("line", "?")),
                v.get("severity", ""),
                v.get("message", v.get("rule_broken", "")),
                v.get("proof_quote", ""),
                v.get("reasoning", ""),
                v.get("fix_suggestion", v.get("suggestion", "")),
            )
        console.print(vt)
    console.print()


# ------------------------------------------------------------------
# Export helpers
# ------------------------------------------------------------------
def _export_json(results: List[Dict[str, Any]], path: Path) -> None:
    clean = []
    for r in results:
        entry = {k: v for k, v in r.items() if k not in ("raw_llm_response",)}
        clean.append(entry)
    path.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")


def _export_csv(results: List[Dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "file",
        "language",
        "score",
        "violations_count",
        "summary",
        "parse_error",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            score = r.get("score", 0)
            writer.writerow(
                {
                    "file": r.get("file", ""),
                    "language": r.get("language", ""),
                    "score": score if not _is_score_na(score) else "N/A",
                    "violations_count": len(r.get("violations", [])),
                    "summary": r.get("summary", r.get("reliability_analysis", "")),
                    "parse_error": "Yes" if r.get("parse_error") else "",
                    "error": r.get("error", ""),
                }
            )


def _save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    dest = Path(output_path)
    ext = dest.suffix.lower()
    if ext == ".json":
        _export_json(results, dest)
    elif ext == ".csv":
        _export_csv(results, dest)
    else:
        console.print(
            f"[red]Unsupported output format '{ext}'.[/red] Use .json or .csv."
        )
        return
    console.print(f"\nResults saved to [bold green]{dest}[/bold green]")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    console.print(
        Panel(
            "[bold cyan]Agentic Static Code Evaluator[/bold cyan]\n"
            "Hybrid deterministic + RAG + LLM analysis  •  Python & C#",
            expand=False,
        )
    )

    # 1. Discover files
    target_path = Path(args.path)
    files = _discover_files(args.path, args.lang)
    if not files:
        console.print("[yellow]No supported source files found.[/yellow]")
        return

    # 2. Display project structure
    _display_project_structure(target_path, files)

    lang_counts: Dict[str, int] = {}
    for f in files:
        lang_counts[f.suffix] = lang_counts.get(f.suffix, 0) + 1
    desc = ", ".join(f"{cnt} {ext}" for ext, cnt in sorted(lang_counts.items()))
    console.print(f"\nFound [bold]{len(files)}[/bold] file(s) to evaluate ({desc}).\n")

    # 3. Initialize components
    llm = LLMClient()

    retriever = None
    if not args.no_rag:
        from src.rag.engine import RuleRetriever
        retriever = RuleRetriever()
        with console.status("[bold green]Ingesting knowledge base …"):
            n_chunks = retriever.ingest()
        console.print(f"Ingested [bold]{n_chunks}[/bold] guideline chunks into ChromaDB.\n")
    else:
        console.print("[yellow]RAG disabled[/yellow] – running without guideline context.\n")

    evaluator = Evaluator(llm_client=llm, rule_retriever=retriever)

    # 4. Evaluate files in parallel
    results: List[Dict[str, Any]] = []
    start = time.perf_counter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task_id: TaskID = progress.add_task("Evaluating …", total=len(files))

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            future_map = {
                pool.submit(evaluator.evaluate, str(f)): f for f in files
            }
            for future in as_completed(future_map):
                file = future_map[future]
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    result = {
                        "file": str(file),
                        "language": "unknown",
                        "score": 0,
                        "summary": "",
                        "violations": [],
                        "error": str(exc),
                    }
                results.append(result)
                progress.advance(task_id)

    elapsed = time.perf_counter() - start

    # 5. Sort by file name
    results.sort(key=lambda r: r.get("file", ""))

    # 6. Print detailed results per file
    for r in results:
        _print_detail(r)

    # 7. Summary table
    _print_summary_table(results)

    # 8. Aggregate stats
    valid_scores = [
        r["score"] for r in results 
        if "error" not in r and not _is_score_na(r.get("score"))
    ]
    parse_error_count = sum(1 for r in results if r.get("parse_error"))
    
    if valid_scores:
        avg = sum(valid_scores) / len(valid_scores)
        color = _score_color(int(avg))
        avg_display = f"[{color}]{avg:.1f}[/{color}]/100"
    else:
        avg_display = "[magenta]N/A[/magenta]"

    stats_line = f"\n[bold]Average Score:[/bold] {avg_display}  | Files: {len(results)}"
    if parse_error_count > 0:
        stats_line += f"  | [magenta]Parse errors: {parse_error_count}[/magenta]"
    stats_line += f"  | Time: {elapsed:.1f}s  | Workers: {args.workers}"
    
    console.print(stats_line)

    # 9. Export results (if requested)
    if args.output:
        _save_results(results, args.output)


if __name__ == "__main__":
    main()
