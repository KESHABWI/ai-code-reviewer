"""The single unified entry point: POST /analyze.

One route handles all three input kinds the person might give it — a GitHub
repo link, a .zip, or one plain file — detects which it got, and routes to
the right underlying flow. Every result is checked against / saved into the
SQLite history (db.py), keyed by commit SHA (GitHub) or content hash (zip/file),
so re-submitting the same commit or the same file instantly returns the
previous result instead of re-running a full review.
"""

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app.config import get_settings
from app.db import AnalysisHistory, find_existing, list_history, save_result
from app.schemas import AnalyzeResponse, FileReview, HistoryEntry, ProjectReview, SourceType
from app.services.github_service import (
    GitHubError,
    download_repo_zip,
    parse_github_url,
    resolve_commit_sha,
)
from app.services.mcp_semantic import prepare_semantic_index
from app.services.ollama_client import OllamaError
from app.services.project_store import ProjectStoreError, content_hash, create_project_from_zip
from app.services.reviewer import review_project, review_single_file

router = APIRouter(tags=["analyze"])


def _record_to_response(record: AnalysisHistory, already_analyzed: bool) -> AnalyzeResponse:
    project_review = None
    file_review = None
    if record.project_id is not None:
        project_review = ProjectReview.model_validate_json(record.review_json)
    else:
        file_review = FileReview.model_validate_json(record.review_json)
    return AnalyzeResponse(
        already_analyzed=already_analyzed,
        source_type=SourceType(record.source_type),
        identifier=record.identifier,
        source_label=record.source_label,
        analyzed_at=record.analyzed_at.isoformat(),
        project_id=record.project_id,
        project_review=project_review,
        file_review=file_review,
    )


def _is_zip(upload: UploadFile) -> bool:
    if upload.filename and upload.filename.lower().endswith(".zip"):
        return True
    return upload.content_type in ("application/zip", "application/x-zip-compressed")


async def _analyze_github(github_url: str) -> AnalyzeResponse:
    try:
        owner, repo, ref = parse_github_url(github_url)
        sha = await resolve_commit_sha(owner, repo, ref)
    except GitHubError as exc:
        raise HTTPException(400, str(exc)) from exc

    existing = await find_existing("github", sha)
    if existing:
        return _record_to_response(existing, already_analyzed=True)

    try:
        zip_bytes = await download_repo_zip(owner, repo, sha)
    except GitHubError as exc:
        raise HTTPException(502, str(exc)) from exc

    try:
        project_id, root = create_project_from_zip(zip_bytes)
    except ProjectStoreError as exc:
        raise HTTPException(400, str(exc)) from exc

    settings = get_settings()
    if settings.code_index_backend == "semantic":
        await prepare_semantic_index(root)

    try:
        result = await review_project(project_id, root)
    except (ValueError, OllamaError) as exc:
        raise HTTPException(400 if isinstance(exc, ValueError) else 502, str(exc)) from exc

    record = await save_result(
        source_type="github",
        identifier=sha,
        source_label=f"{owner}/{repo}",
        review_json=result.model_dump_json(),
        project_id=project_id,
    )
    return _record_to_response(record, already_analyzed=False)


async def _analyze_zip(upload: UploadFile, content: bytes) -> AnalyzeResponse:
    digest = content_hash(content)
    existing = await find_existing("zip", digest)
    if existing:
        return _record_to_response(existing, already_analyzed=True)

    try:
        project_id, root = create_project_from_zip(content)
    except ProjectStoreError as exc:
        raise HTTPException(400, str(exc)) from exc

    settings = get_settings()
    if settings.code_index_backend == "semantic":
        await prepare_semantic_index(root)

    try:
        result = await review_project(project_id, root)
    except (ValueError, OllamaError) as exc:
        raise HTTPException(400 if isinstance(exc, ValueError) else 502, str(exc)) from exc

    record = await save_result(
        source_type="zip",
        identifier=digest,
        source_label=upload.filename or "upload.zip",
        review_json=result.model_dump_json(),
        project_id=project_id,
    )
    return _record_to_response(record, already_analyzed=False)


async def _analyze_file(upload: UploadFile, content: bytes) -> AnalyzeResponse:
    digest = content_hash(content)
    existing = await find_existing("file", digest)
    if existing:
        return _record_to_response(existing, already_analyzed=True)

    filename = upload.filename or "snippet.txt"
    text = content.decode("utf-8", errors="ignore")
    try:
        result = await review_single_file(filename, text)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc

    record = await save_result(
        source_type="file",
        identifier=digest,
        source_label=filename,
        review_json=result.model_dump_json(),
        project_id=None,
    )
    return _record_to_response(record, already_analyzed=False)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile | None = None,
    github_url: str | None = Form(None),
) -> AnalyzeResponse:
    """One input, three kinds of source: a GitHub repo link (github_url), a .zip
    (file, detected by extension/content-type), or a single plain file (file)."""
    provided = [x for x in (file is not None and file.filename, github_url) if x]
    if len(provided) == 0:
        raise HTTPException(400, "Provide either a GitHub repo URL or a file/zip upload")
    if len(provided) > 1:
        raise HTTPException(400, "Provide only one of: GitHub repo URL, file/zip upload")

    if github_url:
        return await _analyze_github(github_url)

    assert file is not None
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Upload exceeds {settings.max_upload_mb}MB limit")

    if _is_zip(file):
        return await _analyze_zip(file, content)
    return await _analyze_file(file, content)


@router.get("/history", response_model=list[HistoryEntry])
async def history(limit: int = 50) -> list[HistoryEntry]:
    records = await list_history(limit)
    return [
        HistoryEntry(
            source_type=SourceType(r.source_type),
            identifier=r.identifier,
            source_label=r.source_label,
            analyzed_at=r.analyzed_at.isoformat(),
        )
        for r in records
    ]
