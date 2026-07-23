# AI Code Reviewer

PR-style code review feedback on demand. Input a GitHub URL, a `.zip` project, a file, or a diff to get line-referenced comments and an overall verdict (**Approve** / **Request Changes** / **Comment**). Grounded with project context via MCP (`code-index-mcp`) and powered by local Ollama models.

## Features

- **Unified Entry Point (`POST /analyze`):** Accepts GitHub repository URLs, `.zip` archives, or single files with automatic mode detection.
- **Commit & Hash Caching:** Results are cached in SQLite keyed by immutable GitHub commit SHAs or SHA256 file hashes to avoid re-reviewing identical code.
- **PR-Focused Verdicts:** Returns structured issues (Bug, Security, Style, Performance, Best Practice) with line numbers, severity ratings, and actionable suggestions.

## MCP Code Indexing

Uses `code-index-mcp` (free, open-source, AST/grep-based) to analyze file symbols and structure without heavy embeddings. Supports an optional semantic backend (`cocoindex-code`).

## Architecture

```
ai-code-reviewer/
├── backend/                 FastAPI service
│   └── app/
│       ├── config.py        pydantic-settings
│       ├── schemas.py       Pydantic models
│       ├── prompts.py       Review prompts
│       ├── db.py            SQLite history storage
│       ├── services/        Ollama, MCP & GitHub clients
│       └── routers/         API endpoints
├── frontend/                Next.js (React + Tailwind) UI
├── streamlit_app.py         Streamlit UI
├── cli/                     `reviewer` CLI tool
├── samples/                 Test sample files
├── scripts/                 Sample output generation script
├── docker-compose.yml
├── Makefile
└── .vscode/tasks.json       VS Code integration tasks
```

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- [Ollama](https://ollama.com) running locally with model pulled (`ollama pull gpt-oss:20b-cloud`)

### Local Setup

```bash
cp .env.example .env
make install          # Install dependencies

make dev-backend      # Terminal 1: FastAPI on http://localhost:8000
make dev-frontend     # Terminal 2: Next.js UI on http://localhost:3000
make dev-streamlit    # Optional Terminal 3: Streamlit UI on http://localhost:8501
```

### Docker Setup

```bash
cp .env.example .env
make docker-up        # Backend on :8000, Next.js UI on :3000
```

## API Reference

| Endpoint               | Method | Purpose                                        |
| ---------------------- | ------ | ---------------------------------------------- |
| `/analyze`             | POST   | Unified entry point (GitHub URL, zip, or file) |
| `/history`             | GET    | List past analyses                             |
| `/projects/upload`     | POST   | Upload a project `.zip` file                   |
| `/review/project/{id}` | POST   | Review all source files in a project           |
| `/review/file`         | POST   | Review a single file in a project              |
| `/review/snippet`      | POST   | Review a standalone code snippet               |
| `/review/diff`         | POST   | Review a before/after code diff                |

Interactive API docs available at `http://localhost:8000/docs`.

## CLI & IDE Integration

Install CLI globally:

```bash
make cli-install      # uv tool install --force ./cli
```

Usage:

```bash
reviewer analyze https://github.com/owner/repo   # GitHub URL
reviewer analyze path/to/project/                # Directory
reviewer analyze path/to/file.py                 # File
reviewer diff before.py after.py                 # Diff
```

**VS Code Task:** Copy `.vscode/tasks.json` into your workspace and run `"Reviewer: review current file"` from the Command Palette.

## Optional Semantic Search (`cocoindex-code`)

To switch from AST to embedding-based search:

```bash
uv tool install --force "cocoindex-code[full]"
```

Set `CODE_INDEX_BACKEND=semantic` in `.env`.

## Test Samples — Real Output

Three test samples reside in `samples/`:

- `clean_sample.py` (Approve)
- `security_issue.py` (Request Changes)
- `logic_bug.py` (Request Changes)

Regenerate sample outputs:

```bash
make dev-backend
uv run python scripts/generate_samples_output.py
```

<!-- SAMPLES:START -->

### Clean sample (expect: mostly Approve, at most minor nitpicks)

**File:** `samples/clean_sample.py`

```python
"""Utilities for working with ordered collections."""

from __future__ import annotations


def deduplicate(items: list[str]) -> list[str]:
    """Return items with duplicates removed, preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def chunk(items: list[str], size: int) -> list[list[str]]:
    """Split items into consecutive chunks of at most `size` elements."""
    if size <= 0:
        raise ValueError("size must be a positive integer")
    return [items[i : i + size] for i in range(0, len(items), size)]

```

**Verdict:** Approve — No issues found.

The module provides straightforward utilities for deduplicating a list of strings while preserving order and for splitting a list into fixed-size chunks, with clear type hints, docstrings, and appropriate error handling.

_No issues found._

---

### Security issue sample (expect: Request Changes)

**File:** `samples/security_issue.py`

```python
"""User lookup against the accounts database."""

import psycopg2

DB_PASSWORD = "SuperSecret123!"  # hardcoded credential, checked straight into source control


def get_user(user_id):
    conn = psycopg2.connect(
        host="prod-db.internal",
        user="admin",
        password=DB_PASSWORD,
        dbname="accounts",
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # string-interpolated SQL
    row = cursor.fetchone()
    conn.close()
    return row

```

**Verdict:** Request Changes — Hardcoded credentials and string-interpolated SQL create severe security vulnerabilities.

The module contains critical security flaws: a hardcoded database password and a SQL query built via string interpolation, exposing the system to credential leakage and SQL injection attacks. These issues must be addressed before merging.

| Line | Category | Severity | Comment                                                                                                          | Suggestion                                                                                         |
| ---- | -------- | -------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 5    | Security | Blocking | Hardcoded database password in source control exposes credentials to anyone with repository access.              | Move the password to an environment variable or a secure secrets manager and load it at runtime.   |
| 13   | Security | Blocking | SQL query uses string interpolation, making it vulnerable to SQL injection if user_id is not strictly validated. | Use parameterized queries, e.g., cursor.execute("SELECT \* FROM users WHERE id = %s", (user_id,)). |

---

### Logic bug sample (expect: Request Changes)

**File:** `samples/logic_bug.py`

```python
"""Duplicate detection and ordering checks for a list of transaction IDs."""


def find_duplicates(t):
    d = []
    for i in range(len(t)):
        for j in range(len(t)):
            if i != j and t[i] == t[j] and t[i] not in d:
                d.append(t[i])
    return d


def is_sorted_ascending(nums):
    for i in range(len(nums)):
        if nums[i] > nums[i + 1]:
            return False
    return True

```

**Verdict:** Request Changes — IndexError due to out-of-range access in is_sorted_ascending.

The module provides duplicate detection and ascending order checks, but contains a critical bug in the sorting function that will raise an exception on the last element. The duplicate finder works but is suboptimal and could be simplified.

| Line | Category | Severity | Comment                                                              | Suggestion                                                                     |
| ---- | -------- | -------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 13   | Bug      | Blocking | Accessing nums[i + 1] when i is the last index causes an IndexError. | Change the loop to for i in range(len(nums) - 1) to avoid out-of-range access. |

<!-- SAMPLES:END -->

## Dev & Maintenance

```bash
make lint      # ruff check .
make format    # ruff --fix + black
```

### Notes & Scope Limits

- File limits: `MAX_FILES_PER_PROJECT` (default 200), `MAX_FILE_SIZE_KB` (default 300).
- Concurrency capped via `REVIEW_CONCURRENCY` (default 3).
- GitHub API: Set `GITHUB_TOKEN` in `.env` for private repos or higher rate limits (>60/hr).
