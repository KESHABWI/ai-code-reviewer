"""CLI for the AI Code Reviewer — designed to be wired into an IDE task/keybinding.

Install globally with:  uv tool install ./cli
Then anywhere:           reviewer analyze https://github.com/owner/repo
                          reviewer analyze path/to/project/       (zips + uploads it)
                          reviewer analyze path/to/file.py
                          reviewer file path/to/file.py
                          reviewer project path/to/project/
                          reviewer diff path/to/before.py path/to/after.py
"""

import os
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Review a file, project, diff, or GitHub link with one command.")
console = Console()

API_URL = os.environ.get("REVIEWER_API_URL", "http://localhost:8000")
_SEVERITY_STYLE = {
    "Blocking": "bold red",
    "Suggestion": "yellow",
    "Nitpick": "blue",
}
_VERDICT_STYLE = {
    "Approve": "bold green",
    "Request Changes": "bold red",
    "Comment": "yellow",
}
IGNORED_DIR_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def _print_review(review: dict) -> None:
    verdict = review["verdict"]
    style = _VERDICT_STYLE.get(verdict, "white")
    console.rule(f"[bold]{review['path']}[/bold] \u2014 [{style}]{verdict}[/{style}]")
    console.print(f"[dim]{review['justification']}[/dim]")
    console.print(review["summary"])
    issues = review.get("issues", [])
    if not issues:
        console.print("[green]No issues found \u2705[/green]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("Line")
    table.add_column("Severity")
    table.add_column("Category")
    table.add_column("Message")
    for issue in issues:
        style = _SEVERITY_STYLE.get(issue["severity"], "white")
        table.add_row(
            str(issue.get("line") or "-"),
            f"[{style}]{issue['severity']}[/{style}]",
            issue["category"],
            issue["message"],
        )
    console.print(table)


@app.command()
def file(path: Path) -> None:
    """Review a single file."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    resp = httpx.post(
        f"{API_URL}/review/snippet",
        json={"filename": path.name, "content": content},
        timeout=180,
    )
    resp.raise_for_status()
    _print_review(resp.json())


@app.command()
def diff(before: Path, after: Path) -> None:
    """Review a before/after pair as a unified diff (stretch goal input)."""
    before_content = before.read_text(encoding="utf-8", errors="ignore")
    after_content = after.read_text(encoding="utf-8", errors="ignore")
    resp = httpx.post(
        f"{API_URL}/review/diff",
        json={"filename": after.name, "before": before_content, "after": after_content},
        timeout=180,
    )
    resp.raise_for_status()
    _print_review(resp.json())


@app.command()
def project(path: Path) -> None:
    """Zip a project directory, upload it, and review every file in it."""
    with TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "project.zip"
        _zip_directory(path, zip_path)

        with console.status("Uploading and indexing project..."):
            with open(zip_path, "rb") as fh:
                upload_resp = httpx.post(
                    f"{API_URL}/projects/upload",
                    files={"file": ("project.zip", fh, "application/zip")},
                    timeout=120,
                )
            upload_resp.raise_for_status()
            project_id = upload_resp.json()["project_id"]

        with console.status(f"Reviewing project {project_id}..."):
            review_resp = httpx.post(f"{API_URL}/review/project/{project_id}", timeout=1200)
            review_resp.raise_for_status()
            result = review_resp.json()

    for fr in result["files"]:
        _print_review(fr)
    console.rule("[bold]Overall[/bold]")
    style = _VERDICT_STYLE.get(result["overall_verdict"], "white")
    console.print(
        f"[{style}]{result['overall_verdict']}[/{style}] \u2014 {result['overall_justification']}"
    )
    console.print(result["overall_summary"])


def _print_overall(result: dict) -> None:
    console.rule("[bold]Overall[/bold]")
    style = _VERDICT_STYLE.get(result["overall_verdict"], "white")
    console.print(
        f"[{style}]{result['overall_verdict']}[/{style}] \u2014 {result['overall_justification']}"
    )
    console.print(result["overall_summary"])


def _zip_directory(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in path.rglob("*"):
            if f.is_file() and not any(part in IGNORED_DIR_PARTS for part in f.parts):
                zf.write(f, f.relative_to(path))


@app.command()
def analyze(target: str) -> None:
    """One command, three kinds of input: a GitHub URL, a directory, or a file.

    Checks history first (by commit SHA for GitHub, content hash otherwise) —
    if it's already been analyzed, prints the saved result instead of re-running.
    """
    is_url = target.startswith(("http://", "https://")) or target.startswith("github.com")
    path = None if is_url else Path(target)

    if is_url:
        with console.status(f"Resolving and analyzing {target}..."):
            resp = httpx.post(f"{API_URL}/analyze", data={"github_url": target}, timeout=900)
    elif path.is_dir():
        with TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "project.zip"
            _zip_directory(path, zip_path)
            with console.status(f"Analyzing project {path}..."), open(zip_path, "rb") as fh:
                resp = httpx.post(
                    f"{API_URL}/analyze",
                    files={"file": ("project.zip", fh, "application/zip")},
                    timeout=900,
                )
    elif path.is_file():
        with console.status(f"Analyzing {path}..."), open(path, "rb") as fh:
            resp = httpx.post(f"{API_URL}/analyze", files={"file": (path.name, fh)}, timeout=900)
    else:
        console.print(f"[red]Not a URL, file, or directory: {target}[/red]")
        raise typer.Exit(1)

    resp.raise_for_status()
    result = resp.json()

    if result["already_analyzed"]:
        console.print(
            f"[yellow]\u23f1\ufe0f  Already analyzed[/yellow] \u2014 "
            f"{result['source_label']} on {result['analyzed_at']}"
        )
    else:
        console.print(f"[green]Analyzed {result['source_label']} just now.[/green]")

    if result.get("project_review"):
        for fr in result["project_review"]["files"]:
            _print_review(fr)
        _print_overall(result["project_review"])
    elif result.get("file_review"):
        _print_review(result["file_review"])


if __name__ == "__main__":
    app()
