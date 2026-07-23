"""Core review orchestration: single-file, diff, and whole-project reviews."""

import asyncio
import difflib
import json
import logging
from pathlib import Path

from app.config import get_settings
from app.prompts import (
    DIFF_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_diff_review_prompt,
    build_file_review_prompt,
    build_project_summary_prompt,
)
from app.schemas import FileReview, ProjectReview
from app.services.mcp_index import code_index_session, extract_text
from app.services.mcp_semantic import semantic_search
from app.services.ollama_client import OllamaClient
from app.services.project_store import list_source_files

logger = logging.getLogger(__name__)


async def review_single_file(file_path: str, content: str) -> FileReview:
    client = OllamaClient()
    prompt = build_file_review_prompt(file_path, content)
    data = await client.chat_json(SYSTEM_PROMPT, prompt)
    return FileReview(path=file_path, language=Path(file_path).suffix.lstrip("."), **data)


async def review_diff(filename: str, before: str, after: str) -> FileReview:
    """Stretch-goal: review a before/after pair as a unified diff."""
    diff_text = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )
    if not diff_text.strip():
        raise ValueError("before and after are identical — nothing to review")
    client = OllamaClient()
    prompt = build_diff_review_prompt(filename, diff_text)
    data = await client.chat_json(DIFF_SYSTEM_PROMPT, prompt)
    return FileReview(path=filename, language=Path(filename).suffix.lstrip("."), **data)


async def _analyze_with_grep_mcp(root: Path, relative_files: list[str]) -> dict[str, str]:
    """Enrich each file with code-index-mcp's per-file analysis (imports, functions)."""
    analyses: dict[str, str] = {}
    async with code_index_session(str(root)) as session:
        for rel_path in relative_files:
            try:
                result = await session.call_tool("analyze_file", {"file_path": rel_path})
                analyses[rel_path] = extract_text(result)
            except Exception as exc:  # noqa: BLE001 - MCP tool call may fail per-file
                logger.warning("code-index-mcp analyze_file failed for %s: %s", rel_path, exc)
                analyses[rel_path] = ""
    return analyses


async def _analyze_with_semantic_mcp(root: Path, relative_files: list[str]) -> dict[str, str]:
    """Enrich each file with cocoindex-code's cross-file semantic search results.

    Unlike the grep backend (which describes a file's own structure), this asks
    "what other code in this project is related to this file?" — surfacing
    related code the reviewer wouldn't otherwise see, at the cost of requiring
    `ccc init` + `ccc index` to have already run for this project (see
    prepare_semantic_index in mcp_semantic.py, called from the upload route).
    """
    analyses: dict[str, str] = {}
    for rel_path in relative_files:
        try:
            query = f"code related to or calling into {rel_path}"
            analyses[rel_path] = await semantic_search(root, query, limit=3)
        except Exception as exc:  # noqa: BLE001 - MCP tool call may fail per-file
            logger.warning("cocoindex-code search failed for %s: %s", rel_path, exc)
            analyses[rel_path] = ""
    return analyses


async def _analyze_with_mcp(root: Path, relative_files: list[str]) -> dict[str, str]:
    settings = get_settings()
    if settings.code_index_backend == "semantic":
        return await _analyze_with_semantic_mcp(root, relative_files)
    return await _analyze_with_grep_mcp(root, relative_files)


async def review_project(project_id: str, root: Path) -> ProjectReview:
    settings = get_settings()
    relative_files = list_source_files(
        root, settings.max_files_per_project, settings.max_file_size_kb
    )

    if not relative_files:
        raise ValueError("No reviewable source files found in the uploaded project")

    file_analyses = await _analyze_with_mcp(root, relative_files)

    semaphore = asyncio.Semaphore(settings.review_concurrency)
    client = OllamaClient()

    async def _review_one(rel_path: str) -> FileReview:
        async with semaphore:
            content = (root / rel_path).read_text(encoding="utf-8", errors="ignore")
            context = file_analyses.get(rel_path) or None
            prompt = build_file_review_prompt(rel_path, content, project_context=context)
            data = await client.chat_json(SYSTEM_PROMPT, prompt)
            return FileReview(path=rel_path, language=Path(rel_path).suffix.lstrip("."), **data)

    file_reviews = await asyncio.gather(*(_review_one(f) for f in relative_files))

    summary_payload = json.dumps([fr.model_dump() for fr in file_reviews])[:12000]
    overall = await client.chat_json(SYSTEM_PROMPT, build_project_summary_prompt(summary_payload))

    return ProjectReview(
        project_id=project_id,
        files=list(file_reviews),
        overall_verdict=overall["overall_verdict"],
        overall_justification=overall["overall_justification"],
        overall_summary=overall["overall_summary"],
    )
