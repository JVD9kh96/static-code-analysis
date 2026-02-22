# Agentic Static Code Evaluator

A hybrid **multi-language** code analysis tool that combines **deterministic static analysis**, **RAG-retrieved coding guidelines**, and a **Multi-Agent "Detective → Judge" Reflection Architecture** to produce a structured Code Quality Score and report for each file.

**Supported languages:** Python and C#.

---

## Overview

The evaluator uses a **Detective → Judge** workflow instead of a single "God Prompt" to reduce hallucinations and improve scoring consistency:

1. **Language Detection** – Auto-detects the language from file extensions (`.py` / `.cs`) or accepts `--lang` to force one.
2. **Deterministic Tools** – Language-specific static analysers run first.
   - *Python*: Pylint, Radon, Bandit, MyPy.
   - *C#*: `dotnet build`, DevSkim, regex-based complexity.
3. **RAG Context** – Retrieves relevant coding rules from a local knowledge base (ChromaDB). Guideline files can cover any language.
4. **Agent A (The Detective)** – Security & Logic Expert. Scans code + security-tool output + RAG for *potential* issues. Allowed to be paranoid; outputs a list of candidates.
5. **Agent B (The Judge)** – Senior Code Reviewer. Takes the Detective's list + filtered lint/build diagnostics, filters false positives, assigns severity (Critical/Major/Minor), and outputs verified violations with a `proof_quote`.
6. **Scoring Engine (Python)** – Deterministic: `100 − penalties`, clamped to [0, 100]. No LLM scoring.

RAG can be disabled with `--no-rag`; the pipeline still runs static tools + both agents, relying on language best practices instead of custom guidelines.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Target Languages | Python, C# |
| Static Analysis (Python) | Pylint, Radon, Bandit, MyPy |
| Static Analysis (C#) | `dotnet build`, DevSkim, regex complexity |
| LLM API | `requests` (OpenAI-compatible `/v1/chat/completions`) |
| Architecture | Multi-Agent (Detective → Judge), Language Profiles |
| RAG / Vector Store | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, CPU) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |
| CLI / Output | Rich (terminal), JSON/CSV export |

---

## Project Structure

```
StaticCodeEval/
├── src/
│   ├── main.py                     # CLI entry point
│   ├── agent/
│   │   ├── llm_client.py           # Generic LLM API client (thread-safe)
│   │   ├── evaluator.py            # Language-agnostic Detective → Judge → Scoring
│   │   └── prompts.py              # Python & C# Detective/Judge prompts
│   ├── languages/
│   │   ├── __init__.py             # Registry: detect_profile(), get_profile()
│   │   ├── base.py                 # LanguageProfile ABC
│   │   ├── python_lang.py          # Python profile (tools, prompts, scoring)
│   │   └── csharp_lang.py          # C# profile (tools, prompts, scoring)
│   ├── rag/
│   │   ├── engine.py               # ChromaDB ingestion & retrieval
│   │   └── embeddings.py           # sentence-transformers wrapper
│   ├── tools/
│   │   ├── analyzer.py             # Python tools: Pylint, Radon, Bandit, MyPy
│   │   └── csharp_analyzer.py      # C# tools: dotnet build, DevSkim, complexity
│   └── utils/
│       └── config.py               # Configuration loader
├── knowledge_base/
│   ├── guidelines.md               # Python coding guidelines (RAG source)
│   └── csharp_guidelines.md        # C# coding guidelines (RAG source)
├── requirements.txt
├── README.md
└── REPORT.md
```

---

## Utilities

### CLI (`python -m src.main`)

| Argument | Description |
|----------|-------------|
| `path` | Path to a single source file or directory (scanned recursively). |
| `--lang` | Force language: `python`, `csharp`, or `auto` (default). |
| `-w`, `--workers` | Number of parallel worker threads (default: 4). |
| `--no-rag` | Disable RAG entirely – no ChromaDB, no guideline retrieval. |
| `-o`, `--output` | Save results to a file (`.json` or `.csv`). |
| `-v`, `--verbose` | Enable DEBUG-level logging. |

### Language Profiles (`src/languages/`)

The `LanguageProfile` ABC defines the contract every language must satisfy:

- `run_tools(file_path)` – run all deterministic analysers.
- `filter_lint(tools)` – reduce lint noise before the Judge sees it.
- `derive_rag_queries(source_code)` – map imports / namespaces to RAG topics.
- `detective_system_prompt` / `judge_system_prompt` – language-tuned prompts.
- `build_detective_user(…)` / `build_judge_user(…)` – format tool results into LLM messages.
- `calculate_score(violations, tools)` – deterministic penalty calculation.

Two profiles are shipped:

- **`PythonProfile`** – wraps Pylint, Radon, Bandit, MyPy; Python Safe Harbor in Judge prompt.
- **`CSharpProfile`** – wraps `dotnet build`, DevSkim, regex complexity; C# Safe Harbor in Judge prompt.

### Static Analysis – Python (`src/tools/analyzer.py`)

`StaticTools` runs deterministic analysers per file:

- **Pylint** – Style, conventions, potential bugs (JSON output).
- **Radon** – Cyclomatic complexity per function/class.
- **Bandit** – Security issues (e.g. unsafe `subprocess`, `eval`).
- **MyPy** – Deterministic type checking (incompatible types, missing returns, etc.).

`filter_pylint_results()` reduces noise by dropping known token-wasters (docstrings, line-too-long, TODO) and convention/refactor messages unless the score is very low.

### Static Analysis – C# (`src/tools/csharp_analyzer.py`)

`CSharpTools` runs deterministic analysers per file:

- **`dotnet build`** – Compiler errors and warnings (auto-locates nearest `.csproj`).
- **DevSkim** – Microsoft security linter (SARIF output).
- **Regex complexity** – Estimates cyclomatic complexity per method by counting branching keywords (`if`, `case`, `for`, `foreach`, `while`, `catch`, `&&`, `||`, `??`).

`filter_build_diagnostics()` drops low-value build warnings (e.g. CS1591 missing XML comment).

### LLM Client (`src/agent/llm_client.py`)

`LLMClient` is a model-agnostic, thread-safe wrapper around any OpenAI-compatible chat endpoint. Swap models by setting:

- `LLM_API_URL` – Endpoint URL (e.g. `http://host:port/v1/chat/completions`).
- `LLM_MODEL` – Model identifier (e.g. `gemma`, `deepseek-coder`).

Retries with exponential backoff on transient failures.

### RAG Engine (`src/rag/engine.py`)

`RuleRetriever`:

- **Ingest** – Reads `*.md` files under `knowledge_base/`, splits on `##` headers, embeds chunks, and stores them in ChromaDB.
- **Retrieve** – Given a query (e.g. "database rules"), returns the top-K most relevant chunks via semantic similarity.

Embeddings use `sentence-transformers/all-MiniLM-L6-v2` locally (no LLM calls for embeddings). Both Python and C# guidelines live in `knowledge_base/` and are ingested together.

### Evaluator (`src/agent/evaluator.py`)

Language-agnostic **Detective → Judge** pipeline. For each file:

1. Auto-detect language → obtain `LanguageProfile`.
2. Run language-specific tools via `profile.run_tools()`.
3. Filter lint/build noise via `profile.filter_lint()`.
4. Retrieve RAG guidelines (if enabled).
5. **Detective** – Code + security-tool output + RAG → `potential_issues`. Explicitly flags use of insecure RNG for secrets.
6. **Judge** – Code + `potential_issues` + filtered lint/build → `verified_violations` with `proof_quote`, `reasoning` (CoT), and `analysis_summary`. Forced to reason before assigning severity.
7. **Scoring** – `profile.calculate_score()`.

### Prompts (`src/agent/prompts.py`)

**Python prompts:**
- `DETECTIVE_SYSTEM_PROMPT` – Security & Logic Expert for Python. Includes explicit cryptography rule (flag `random` module for secrets).
- `JUDGE_SYSTEM_PROMPT` – Senior Python Security Auditor with **Chain-of-Thought** (`reasoning` field before `severity`) and expanded Safe Harbor (big ints, `re.compile`, f-strings, argparse, threading, EAFP file handling, CLI argument safety, literal-math division).

**C# prompts:**
- `CS_DETECTIVE_SYSTEM_PROMPT` – Security & Logic Expert for C# / .NET. Includes explicit cryptography rule (flag `System.Random` for secrets).
- `CS_JUDGE_SYSTEM_PROMPT` – Senior C# Security Auditor with **Chain-of-Thought** (`reasoning` field before `severity`) and Safe Harbor (`async void` in event handlers, `string.Format`, LINQ materialisation, `lock`, nullable refs, `IDisposable`).

### Scoring (Deterministic)

| Penalty | Amount |
|---------|--------|
| Critical violation | −15 |
| Major violation | −7 |
| Minor violation | −2 |
| Cyclomatic complexity > 15 | −5 |

Start: 100. Result clamped to [0, 100]. Same formula for both languages.

### Configuration (`src/utils/config.py`)

All settings are loaded from environment variables. See the table below.

---

## Installation

```bash
pip install -r requirements.txt
```

For **C# support**, install the .NET SDK and optionally DevSkim:

```bash
# .NET SDK (provides dotnet build)
# Download from https://dotnet.microsoft.com/download

# DevSkim security linter (optional but recommended)
dotnet tool install -g Microsoft.CST.DevSkim.CLI
```

---

## Usage

```bash
# Evaluate a directory (auto-detect Python + C# files)
python -m src.main ./my_project

# Force Python-only scan
python -m src.main ./my_project --lang python

# Force C#-only scan
python -m src.main ./my_project --lang csharp

# Single file (language detected from extension)
python -m src.main ./app/main.py
python -m src.main ./src/Program.cs

# More workers, no RAG
python -m src.main ./my_project -w 8 --no-rag

# Export results
python -m src.main ./my_project -o report.json
python -m src.main ./my_project -o report.csv
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_URL` | `http://87.236.166.36:8082/v1/chat/completions` | Chat completions endpoint |
| `LLM_MODEL` | `gemma` | Model identifier |
| `LLM_TEMPERATURE` | `0.2` | Sampling temperature |
| `LLM_MAX_TOKENS` | `2048` | Max response tokens |
| `LLM_TIMEOUT` | `120` | Request timeout (seconds) |
| `LLM_MAX_RETRIES` | `3` | Retries on failure |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `CHROMA_PERSIST_DIR` | `.chromadb/` | ChromaDB persistence path |
| `KNOWLEDGE_BASE_PATH` | `knowledge_base/` | Path to guidelines Markdown |
| `RAG_TOP_K` | `3` | Number of guideline chunks per query |
| `MAX_WORKERS` | `4` | Default thread pool size |

---

## Output Formats

### JSON (`-o report.json`)

Full per-file results: `file`, `language`, `score`, `summary`, `violations` (array of `{line, message, proof_quote, reasoning, severity, fix_suggestion}`), and `error` if applicable.

### CSV (`-o report.csv`)

Flat summary: `file`, `language`, `score`, `violations_count`, `summary`, `error`.

---

## Customizing Guidelines

Edit or add `.md` files under `knowledge_base/`. Structure rules under `##` headers; each header section becomes a retrievable chunk. Both Python and C# guidelines are ingested together — the RAG engine retrieves whichever chunks are most relevant to the code being analysed. Re-run the tool; RAG ingestion runs automatically unless `--no-rag` is used.

---

## Adding a New Language

1. Create a tool wrapper in `src/tools/` (like `csharp_analyzer.py`).
2. Add prompts to `src/agent/prompts.py` (Detective + Judge system/user templates with language-specific Safe Harbor).
3. Create a `LanguageProfile` subclass in `src/languages/` implementing all abstract methods.
4. Register the extension → profile mapping in `src/languages/__init__.py`.
5. Add a guideline file to `knowledge_base/`.

---

## Swapping LLM Backends

Point the client at any OpenAI-compatible endpoint:

```bash
# DeepSeek
set LLM_API_URL=https://api.deepseek.com/v1/chat/completions
set LLM_MODEL=deepseek-coder

# Local Ollama
set LLM_API_URL=http://localhost:11434/v1/chat/completions
set LLM_MODEL=codellama

python -m src.main ./my_project
```
