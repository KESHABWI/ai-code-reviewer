"""Zip extraction and safe filesystem access for uploaded projects."""

import hashlib
import shutil
import uuid
import zipfile
from pathlib import Path

from app.config import get_settings

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".kt",
    ".swift",
    ".sql",
    ".vue",
}
IGNORED_DIR_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


class ProjectStoreError(Exception):
    pass


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in zf.infolist():
        member_path = (dest / member.filename).resolve()
        if not str(member_path).startswith(str(dest_resolved)):
            raise ProjectStoreError(f"Unsafe path in zip archive: {member.filename}")
    zf.extractall(dest)


def create_project_from_zip(zip_bytes: bytes) -> tuple[str, Path]:
    settings = get_settings()
    project_id = uuid.uuid4().hex[:12]
    dest = Path(settings.projects_dir) / project_id
    dest.mkdir(parents=True, exist_ok=True)

    zip_path = dest / "_upload.zip"
    zip_path.write_bytes(zip_bytes)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            _safe_extract(zf, dest)
    except zipfile.BadZipFile as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise ProjectStoreError("Uploaded file is not a valid zip archive") from exc
    finally:
        zip_path.unlink(missing_ok=True)

    flatten_single_root(dest)
    return project_id, dest


def project_path(project_id: str) -> Path:
    settings = get_settings()
    path = Path(settings.projects_dir) / project_id
    if not path.exists():
        raise ProjectStoreError(f"Unknown project_id: {project_id}")
    return path


def content_hash(data: bytes) -> str:
    """A stable identifier for zip/file uploads, used as the history dedupe key —
    the same role a commit SHA plays for a GitHub-sourced project."""
    return hashlib.sha256(data).hexdigest()


def flatten_single_root(dest: Path) -> None:
    """If `dest` contains exactly one entry and it's a directory — true for every
    GitHub codeload zip ('{repo}-{sha}/...') and common for manually-zipped
    projects too — move its contents up so `dest` itself is the real project
    root. Applied right after every extraction so project_path() always points
    at the actual source tree, regardless of where the zip came from."""
    entries = list(dest.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        wrapper = entries[0]
        for child in wrapper.iterdir():
            shutil.move(str(child), str(dest / child.name))
        wrapper.rmdir()


def list_source_files(root: Path, max_files: int, max_size_kb: int) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            break
        if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
            continue
        if any(part in IGNORED_DIR_PARTS for part in path.parts):
            continue
        if path.stat().st_size > max_size_kb * 1024:
            continue
        files.append(str(path.relative_to(root)))
    return files
