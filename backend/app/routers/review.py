from fastapi import APIRouter, HTTPException

from app.schemas import (
    DiffReviewRequest,
    FileReview,
    FileReviewRequest,
    ProjectReview,
    SnippetReviewRequest,
)
from app.services.ollama_client import OllamaError
from app.services.project_store import ProjectStoreError, project_path
from app.services.reviewer import review_diff, review_project, review_single_file

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/project/{project_id}", response_model=ProjectReview)
async def review_whole_project(project_id: str) -> ProjectReview:
    try:
        root = project_path(project_id)
    except ProjectStoreError as exc:
        raise HTTPException(404, str(exc)) from exc
    try:
        return await review_project(project_id, root)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/file", response_model=FileReview)
async def review_file_in_project(payload: FileReviewRequest) -> FileReview:
    try:
        root = project_path(payload.project_id)
    except ProjectStoreError as exc:
        raise HTTPException(404, str(exc)) from exc

    target = (root / payload.file_path).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.is_file():
        raise HTTPException(404, "File not found in project")

    content = target.read_text(encoding="utf-8", errors="ignore")
    try:
        return await review_single_file(payload.file_path, content)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/snippet", response_model=FileReview)
async def review_snippet(payload: SnippetReviewRequest) -> FileReview:
    try:
        return await review_single_file(payload.filename, payload.content)
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/diff", response_model=FileReview)
async def review_diff_endpoint(payload: DiffReviewRequest) -> FileReview:
    """Stretch-goal input: review a before/after pair as a unified diff."""
    try:
        return await review_diff(payload.filename, payload.before, payload.after)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(502, str(exc)) from exc
