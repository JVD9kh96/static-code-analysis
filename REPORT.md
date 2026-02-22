# Agentic Static Code Evaluator – Architecture Report

This document describes every component in the evaluation pipeline: what it does, what goes in, what comes out, what issues it catches, and example outputs.

**Supported languages:** Python and C#.

---

## Pipeline Block Diagram

```
                          ┌──────────────┐
                          │ Source File   │
                          │ (.py / .cs)  │
                          └──────┬───────┘
                                 │
                          ┌──────▼───────┐
                          │  Language    │
                          │  Detection  │
                          │  (registry) │
                          └──────┬───────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
          ┌─── Python Profile ────┐   ┌──── C# Profile ──────┐
          │                       │   │                       │
          │  ┌───────────────┐    │   │  ┌───────────────┐    │
          │  │    Pylint     │    │   │  │  dotnet build │    │
          │  └───────┬───────┘    │   │  └───────┬───────┘    │
          │          ▼            │   │          ▼            │
          │  ┌───────────────┐    │   │  ┌───────────────┐    │
          │  │ Pylint Filter │    │   │  │  Build Filter │    │
          │  └───────┬───────┘    │   │  └───────┬───────┘    │
          │          │            │   │          │            │
          │  ┌───────────────┐    │   │  ┌───────────────┐    │
          │  │     Radon     │    │   │  │   DevSkim     │    │
          │  └───────┬───────┘    │   │  └───────┬───────┘    │
          │          │            │   │          │            │
          │  ┌───────────────┐    │   │  ┌───────────────┐    │
          │  │    Bandit     │    │   │  │  Regex CC     │    │
          │  └───────┬───────┘    │   │  └───────┬───────┘    │
          │          │            │   │          │            │
          │  ┌───────────────┐    │   └──────────┼────────────┘
          │  │     MyPy      │    │              │
          │  └───────┬───────┘    │              │
          │          │            │              │
          └──────────┼────────────┘              │
                     │                           │
                     └─────────┬─────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │  Semgrep (shared) │
                     │  pattern scanner  │
                     └─────────┬─────────┘
                               │
                     ┌─────────▼─────────┐
                     │  RAG Engine       │
                     │  (optional)       │
                     └─────────┬─────────┘
                               │
                     ┌─────────▼─────────────────┐
                     │  Agent A: Detective (LLM) │
                     │  IN:  Code + security     │
                     │       tool + Semgrep + RAG│
                     │  OUT: potential_issues[]   │
                     └─────────┬─────────────────┘
                               │
                     ┌─────────▼─────────────────┐
                     │  Agent B: Judge (LLM)     │
                     │  IN:  Code + potential_   │
                     │       issues + lint/build │
                     │       + Semgrep           │
                     │  OUT: verified_violations │
                     │       + analysis_summary  │
                     └─────────┬─────────────────┘
                               │
                     ┌─────────▼─────────────────┐
                     │  Scoring Engine (Python)  │
                     │  IN:  violations +        │
                     │       complexity data     │
                     │  OUT: score 0–100         │
                     └─────────┬─────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │  Final Report     │
                     │  (Rich/JSON/CSV)  │
                     └───────────────────┘
```

---

## Language Profile System

The `LanguageProfile` ABC (`src/languages/base.py`) decouples the pipeline from any single language. Each profile implements:

| Method / Property | Purpose |
|---|---|
| `name`, `extensions` | Metadata for display and file discovery |
| `run_tools(file_path)` | Run all deterministic analysers |
| `filter_lint(tools)` | Remove noise from lint / build diagnostics |
| `derive_rag_queries(source)` | Map code patterns → RAG topics |
| `detective_system_prompt` | Language-tuned system prompt for Agent A |
| `judge_system_prompt` | Language-tuned system prompt for Agent B (with Safe Harbor) |
| `build_detective_user(…)` | Format tool results into Detective's user message |
| `build_judge_user(…)` | Format tool results into Judge's user message |
| `calculate_score(violations, tools)` | Deterministic penalty calculation |

Registered profiles are resolved by `detect_profile(file_path)` in `src/languages/__init__.py`.

---

## Python Components

---

### 1. Pylint

| Property | Value |
|----------|-------|
| **Type** | Deterministic static analysis |
| **Source** | `src/tools/analyzer.py` → `StaticTools.run_pylint()` |
| **Input** | File path to a single `.py` file |
| **Output** | `{"score": float, "messages": [...], "error": str\|None}` |
| **Issues Detected** | Undefined variables, unused imports, unreachable code, bad formatting, type mismatches, missing return statements |
| **Message Types** | Words: `fatal`, `error`, `warning`, `convention`, `refactor` |
| **Used By** | Judge agent (after filtering) |

**Example Output:**

```json
{
  "score": 6.5,
  "messages": [
    {
      "type": "error",
      "message_id": "E0602",
      "module": "app",
      "line": 12,
      "column": 4,
      "message": "Undefined variable 'db_conn'",
      "symbol": "undefined-variable"
    }
  ],
  "error": null
}
```

---

### 2. Pylint Filter

| Property | Value |
|----------|-------|
| **Type** | Deterministic post-processing |
| **Source** | `src/tools/analyzer.py` → `StaticTools.filter_pylint_results()` |
| **Input** | Raw Pylint result dict |
| **Output** | Same structure, with noise removed |
| **Logic** | Drop known token-waster message IDs (C0114–C0116, C0301, W0511, R0903, R0913). Keep `fatal`/`error`/`warning`. Drop `convention`/`refactor` unless score < 5.0. |

---

### 3. Radon

| Property | Value |
|----------|-------|
| **Type** | Deterministic complexity analysis |
| **Source** | `src/tools/analyzer.py` → `StaticTools.run_radon()` |
| **Input** | File path to a single `.py` file |
| **Output** | `{"blocks": [...], "average_complexity": float, "error": str\|None}` |
| **Issues Detected** | High cyclomatic complexity |
| **Ranks** | `A` (1–5), `B` (6–10), `C` (11–15), `D` (16–20), `E/F` (21+) |
| **Used By** | Scoring Engine (penalty if complexity > 15) |

---

### 4. Bandit

| Property | Value |
|----------|-------|
| **Type** | Deterministic security linting |
| **Source** | `src/tools/analyzer.py` → `StaticTools.run_bandit()` |
| **Input** | File path to a single `.py` file |
| **Output** | `{"issues": [...], "metrics": {...}, "error": str\|None}` |
| **Issues Detected** | SQL injection, command injection, `eval()`/`exec()`, hardcoded passwords, weak crypto, insecure `random`, `assert` in production |
| **Used By** | Detective agent |

---

### 5. MyPy

| Property | Value |
|----------|-------|
| **Type** | Deterministic type checking |
| **Source** | `src/tools/analyzer.py` → `StaticTools.run_mypy()` |
| **Input** | File path to a single `.py` file |
| **Output** | `{"errors": [{"line", "message", "code"}], "error": str\|None}` |
| **Issues Detected** | Incompatible types, missing returns, incorrect argument types, unsafe Optional usage |
| **Used By** | Judge agent |

---

### 6. Semgrep (Shared – both languages)

| Property | Value |
|----------|-------|
| **Type** | Pattern-based static analysis (language-agnostic) |
| **Source** | `src/tools/semgrep_analyzer.py` → `run_semgrep()` |
| **Input** | File path to any supported source file |
| **Output** | `{"findings": [{"rule_id", "severity", "message", "line", "end_line", "category"}], "error": str\|None}` |
| **Issues Detected** | Security vulnerabilities, correctness bugs, best-practice violations — driven by community rulesets (`--config auto`) |
| **Config** | Default `auto` (community rules, cached after first fetch). Can be overridden with local YAML or registry entries like `p/python`, `p/csharp`. |
| **Used By** | Both Detective and Judge agents (high-signal deterministic evidence) |

**Example Output:**

```json
{
  "findings": [
    {
      "rule_id": "python.lang.security.audit.dangerous-subprocess-use",
      "severity": "WARNING",
      "message": "Detected subprocess call with shell=True",
      "line": 34,
      "end_line": 34,
      "category": "security"
    },
    {
      "rule_id": "python.lang.security.audit.hardcoded-password-default-arg",
      "severity": "ERROR",
      "message": "Detected hardcoded password used as default argument",
      "line": 8,
      "end_line": 8,
      "category": "security"
    }
  ],
  "error": null
}
```

---

### 7. Python Detective (Agent A)

| Property | Value |
|----------|-------|
| **Role** | Security & Logic Expert for Python |
| **Input** | Source code + Bandit results + Semgrep findings + RAG guidelines |
| **Output** | `[{"line", "issue", "type": "Security\|Logic\|Pattern"}]` |
| **Behavior** | Paranoid — flags anything suspicious. Won't flag safe Python features unless in a dangerous context. |
| **Cryptography Rule** | ALWAYS flags `random` module (`random.choice`, `random.randint`, etc.) when used for tokens, passwords, or session IDs. Requires `secrets` instead. |

---

### 8. Python Judge (Agent B)

| Property | Value |
|----------|-------|
| **Role** | Senior Python Security Auditor |
| **Input** | Code + potential_issues + filtered Pylint + MyPy + Semgrep |
| **Output** | `{"verified_violations": [...], "analysis_summary": str}` |
| **Safe Harbor** | Python 3 big ints, `re.compile()`, f-strings (display only), argparse, thread start/join, EAFP file handling, CLI argument safety, literal-math division |
| **Chain-of-Thought** | Each violation requires a `reasoning` field (written before `severity`) explaining exactly why the quoted code is a real flaw. If reasoning reveals the issue is not real, the entry must be dropped. |
| **Requires** | `proof_quote` + `reasoning` for every kept violation |

---

## C# Components

---

### 9. dotnet build

| Property | Value |
|----------|-------|
| **Type** | Deterministic compiler diagnostics |
| **Source** | `src/tools/csharp_analyzer.py` → `CSharpTools.run_dotnet_build()` |
| **Input** | File path to a `.cs` file (auto-locates nearest `.csproj`) |
| **Output** | `{"diagnostics": [{"id", "severity", "message", "line", "column"}], "error": str\|None}` |
| **Issues Detected** | Compilation errors (CS****), type mismatches, nullable warnings, missing references |
| **Used By** | Judge agent (after filtering) |

**Example Output:**

```json
{
  "diagnostics": [
    {
      "id": "CS0029",
      "severity": "error",
      "message": "Cannot implicitly convert type 'string' to 'int'",
      "line": 15,
      "column": 20
    },
    {
      "id": "CS8600",
      "severity": "warning",
      "message": "Converting null literal or possible null value to non-nullable type",
      "line": 42,
      "column": 12
    }
  ],
  "error": null
}
```

---

### 10. Build Diagnostics Filter

| Property | Value |
|----------|-------|
| **Type** | Deterministic post-processing |
| **Source** | `src/tools/csharp_analyzer.py` → `CSharpTools.filter_build_diagnostics()` |
| **Input** | Raw `dotnet build` result dict |
| **Output** | Same structure, with noise removed |
| **Logic** | Drop CS1591 (missing XML comment). |

---

### 11. DevSkim

| Property | Value |
|----------|-------|
| **Type** | Deterministic security linting |
| **Source** | `src/tools/csharp_analyzer.py` → `CSharpTools.run_devskim()` |
| **Input** | File path to a single `.cs` file |
| **Output** | `{"issues": [{"rule_id", "severity", "description", "line_number"}], "error": str\|None}` |
| **Issues Detected** | SQL injection, command injection, insecure deserialization, hardcoded secrets, weak cryptography, insecure HTTP |
| **Used By** | Detective agent |

**Example Output:**

```json
{
  "issues": [
    {
      "rule_id": "DS104456",
      "severity": "error",
      "description": "SQL injection: string concatenation used in SQL command",
      "line_number": 28
    }
  ],
  "error": null
}
```

---

### 12. Regex Complexity (C#)

| Property | Value |
|----------|-------|
| **Type** | Heuristic complexity analysis |
| **Source** | `src/tools/csharp_analyzer.py` → `CSharpTools.run_complexity()` |
| **Input** | File path to a single `.cs` file |
| **Output** | `{"blocks": [{"name", "type", "complexity", "rank", "lineno"}], "average_complexity": float, "error": str\|None}` |
| **Method** | Counts branching keywords per method: `if`, `else if`, `case`, `for`, `foreach`, `while`, `do`, `catch`, `&&`, `\|\|`, `??` |
| **Ranks** | `A` (≤5), `B` (6–10), `C` (11–20), `D` (>20) |
| **Used By** | Scoring Engine (penalty if complexity > 15) |

**Example Output:**

```json
{
  "blocks": [
    {
      "name": "ProcessOrder",
      "type": "method",
      "complexity": 12,
      "rank": "C",
      "lineno": 35
    }
  ],
  "average_complexity": 12.0,
  "error": null
}
```

---

### 13. C# Detective (Agent A)

| Property | Value |
|----------|-------|
| **Role** | Security & Logic Expert for C# / .NET |
| **Input** | Source code + DevSkim results + Semgrep findings + RAG guidelines |
| **Output** | `[{"line", "issue", "type": "Security\|Logic\|Pattern"}]` |
| **Behavior** | Paranoid. Won't flag standard C# features (async/await, LINQ, `string.Format`, null-conditional) unless in a dangerous context. |
| **Cryptography Rule** | ALWAYS flags `System.Random` when used for tokens, passwords, or session IDs. Requires `RandomNumberGenerator` instead. |

---

### 14. C# Judge (Agent B)

| Property | Value |
|----------|-------|
| **Role** | Senior C# / .NET Security Auditor |
| **Input** | Code + potential_issues + filtered build diagnostics + Semgrep |
| **Output** | `{"verified_violations": [...], "analysis_summary": str}` |
| **Safe Harbor** | `async void` in event handlers, `string.Format` (display only), LINQ `.ToList()`, `lock`, nullable refs, `IDisposable` in `using`, singleton `HttpClient` in console apps |
| **Chain-of-Thought** | Each violation requires a `reasoning` field (written before `severity`) explaining exactly why the quoted code is a real flaw. If reasoning reveals the issue is not real, the entry must be dropped. |
| **Requires** | `proof_quote` + `reasoning` for every kept violation |

**Example Output:**

```json
{
  "verified_violations": [
    {
      "line": 28,
      "message": "SQL injection via string concatenation in SqlCommand",
      "proof_quote": "cmd.CommandText = \"SELECT * FROM Users WHERE Id = \" + userId;",
      "reasoning": "The variable userId comes from user input and is concatenated directly into the SQL string without parameterisation. An attacker can inject arbitrary SQL via the userId parameter.",
      "severity": "Critical",
      "fix_suggestion": "Use parameterised queries: cmd.Parameters.AddWithValue(\"@id\", userId)"
    },
    {
      "line": 65,
      "message": "HttpClient created inside a loop causes socket exhaustion",
      "proof_quote": "var client = new HttpClient();",
      "reasoning": "HttpClient implements IDisposable but its underlying socket is not released immediately on Dispose(). Creating a new instance per iteration in a loop will exhaust the OS socket pool under load.",
      "severity": "Major",
      "fix_suggestion": "Inject IHttpClientFactory or use a static/shared HttpClient instance"
    }
  ],
  "analysis_summary": "Critical SQL injection vulnerability at line 28. HttpClient misuse will cause socket exhaustion under load."
}
```

---

## Shared Components

---

### 15. RAG Engine (Optional)

| Property | Value |
|----------|-------|
| **Type** | Retrieval-Augmented Generation (semantic search) |
| **Source** | `src/rag/engine.py` → `RuleRetriever` |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (local, CPU) |
| **Vector Store** | ChromaDB (persistent) |
| **Input** | Query strings derived from code patterns (language-specific) |
| **Output** | Top-K Markdown chunks from `knowledge_base/*.md` |
| **Can be disabled** | `--no-rag` flag |

**Python Query Map (examples):**

| Code Contains | RAG Query |
|---------------|-----------|
| `import sqlalchemy` | "database rules" |
| `import subprocess` | "security subprocess rules" |
| `print(...)` | "logging rules" |
| `import threading` | "concurrency rules" |

**C# Query Map (examples):**

| Code Contains | RAG Query |
|---------------|-----------|
| `System.Data.SqlClient` | "database rules" |
| `Process.Start` | "security subprocess rules" |
| `Console.Write` | "logging rules" |
| `HttpClient` | "error handling rules" |
| `BinaryFormatter` | "security deserialization rules" |

---

### 16. Scoring Engine

| Property | Value |
|----------|-------|
| **Type** | Deterministic Python logic (no LLM) |
| **Source** | Each `LanguageProfile.calculate_score()` |
| **Input** | `verified_violations` (from Judge) + complexity data |
| **Output** | Integer score, 0–100 |

**Penalty Table (same for both languages):**

| Condition | Penalty |
|-----------|---------|
| Each `Critical` violation | −15 |
| Each `Major` violation | −7 |
| Each `Minor` violation | −2 |
| Any function/method with cyclomatic complexity > 15 | −5 (once) |

**Formula:** `score = max(0, min(100, 100 − sum(penalties)))`

---

### 17. Final Report

| Property | Value |
|----------|-------|
| **Type** | Output formatter |
| **Source** | `src/main.py` |
| **Terminal** | Rich panels + color-coded summary table (includes Language and Reasoning columns) |
| **JSON Export** | `file`, `language`, `score`, `summary`, `violations[]` (includes `proof_quote`, `reasoning`), `error` |
| **CSV Export** | `file`, `language`, `score`, `violations_count`, `summary`, `error` |

**Example Terminal Output:**

```
╭──────────────────────────────────────────────────╮
│ Agentic Static Code Evaluator                    │
│ Hybrid deterministic + RAG + LLM analysis        │
│ Python & C#                                      │
╰──────────────────────────────────────────────────╯
Found 5 file(s) to evaluate (3 .py, 2 .cs).

╭─ app.py [Python]  Score: 63/100 ─╮
│  Summary: Two critical security issues.          │
╰──────────────────────────────────────────────────╯
  Line  Severity  Message               Proof                            Reasoning                          Fix
    34  Critical  shell=True injection   subprocess.run(..., shell=True)  User-controlled cmd string ...     Use shell=False
     8  Critical  Hardcoded password     PASSWORD = "admin123"            Secret is plaintext in source ...  Use os.getenv()

╭─ Program.cs [C#]  Score: 78/100 ─╮
│  Summary: SQL injection at line 28.              │
╰──────────────────────────────────────────────────╯
  Line  Severity  Message               Proof                            Reasoning                          Fix
    28  Critical  SQL injection          "SELECT * WHERE Id=" + userId    userId from user input concat...   Use parameters
    65  Major     HttpClient in loop     new HttpClient()                 Socket pool exhaustion under...    Use factory

┌──────────── Evaluation Summary ──────────────┐
│  #  │ File        │ Lang   │ Score │ Violations│
├─────┼─────────────┼────────┼───────┼───────────┤
│   1 │ app.py      │ Python │   63  │     2     │
│   2 │ utils.py    │ Python │   93  │     1     │
│   3 │ db.py       │ Python │   78  │     2     │
│   4 │ Program.cs  │ C#     │   78  │     2     │
│   5 │ Service.cs  │ C#     │   95  │     0     │
└─────┴─────────────┴────────┴───────┴───────────┘

Average Score: 81.4/100  | Files: 5  | Time: 18.2s  | Workers: 4
```

---

## Data Flow Summary

```
 Source file (.py / .cs)
    │
    ├──► Language Detection ──► LanguageProfile
    │
    ├──► [Python]                               [C#]
    │    Pylint → filter ──────────────┐        dotnet build → filter ──────────┐
    │    Radon ─────────────────────┐  │        DevSkim ──────────────┐         │
    │    MyPy ──────────────────┐   │  │        Regex CC ──────────┐  │         │
    │    Bandit ─────────────┐  │   │  │                           │  │         │
    │                        │  │   │  │                           │  │         │
    ├──► RAG Engine ──┐      │  │   │  │                    ┌──────┘  │         │
    │                 │      │  │   │  │                    │         │         │
    │                 ▼      ▼  │   │  │                    ▼         │         │
    │         ┌──────────────────┐  │  │           ┌──────────────────┐         │
    │         │  Detective (LLM) │  │  │           │  Detective (LLM) │         │
    │         │  → potential_    │  │  │           │  → potential_    │         │
    │         │    issues[]     │  │  │           │    issues[]     │         │
    │         └────────┬────────┘  │  │           └────────┬────────┘         │
    │                  │           │  │                    │                  │
    │                  ▼           ▼  ▼                    ▼                  ▼
    │         ┌──────────────────────────┐        ┌──────────────────────────┐
    │         │  Judge (LLM)            │        │  Judge (LLM)            │
    │         │  → verified_violations  │        │  → verified_violations  │
    │         └────────┬────────────────┘        └────────┬────────────────┘
    │                  │                                  │
    │                  ▼                                  ▼
    │         ┌──────────────────┐                ┌──────────────────┐
    │         │  Scoring Engine  │                │  Scoring Engine  │
    │         │  → score 0–100   │                │  → score 0–100   │
    │         └────────┬─────────┘                └────────┬─────────┘
    │                  │                                  │
    │                  └────────────┬──────────────────────┘
    │                               │
    │                     ┌─────────▼─────────┐
    │                     │  Report Output   │
    │                     │  (Rich/JSON/CSV) │
    │                     └──────────────────┘
```

---

## Why This Architecture?

| Problem with single-prompt | How Detective → Judge + Language Profiles solves it |
|---|---|
| LLM invents bugs that don't exist | Judge cross-references line numbers with actual code; discards mismatches |
| LLM assigns severity before thinking it through | CoT `reasoning` field is written **before** `severity`, forcing the LLM to justify the flaw first — and drop it when reasoning reveals it's not real (e.g., dividing by a non-zero literal) |
| Inconsistent scoring across runs | Scoring is deterministic Python math, not LLM opinion |
| LLM ignores tool output | Detective is forced to address security-tool findings; Judge is forced to address lint/build diagnostics, and must provide `proof_quote` evidence |
| LLM applies C/Java paradigms to Python | Expanded Safe Harbor bans false patterns: EAFP file handling, CLI argument safety, literal-math division |
| Too many trivial issues drown real bugs | Lint/build filter removes noise; Judge filters trivial findings; Detective ignores styling |
| LLM misses cryptographic weakness | Detective has explicit rule to flag `random` module (Python) / `System.Random` (C#) for token/password generation |
| No company-specific rules | RAG retrieves relevant guidelines; Detective checks compliance |
| Hard to add new languages | `LanguageProfile` ABC isolates language-specific logic; core pipeline is language-agnostic |
| Language-specific LLM hallucinations | Safe Harbor lists are tuned per language (Python big ints vs C# async void) |
