from fastapi import APIRouter, HTTPException, UploadFile

from app.config import get_settings
from app.schemas import UploadResponse
from app.services.mcp_semantic import prepare_semantic_index
from app.services.project_store import ProjectStoreError, create_project_from_zip, list_source_files

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/upload", response_model=UploadResponse)
async def upload_project(file: UploadFile) -> UploadResponse:
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Zip exceeds {settings.max_upload_mb}MB limit")

    try:
        project_id, root = create_project_from_zip(content)
    except ProjectStoreError as exc:
        raise HTTPException(400, str(exc)) from exc

    files = list_source_files(root, settings.max_files_per_project, settings.max_file_size_kb)

    if settings.code_index_backend == "semantic":
        # Builds the cocoindex-code index once, up front, so every later search
        # against this project is fast. This is the cost grep-based indexing
        # doesn't have — see mcp_semantic.py's module docstring.
        await prepare_semantic_index(root)

    return UploadResponse(project_id=project_id, file_count=len(files), files=files)
