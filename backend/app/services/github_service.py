"""Fetches a public GitHub repo as a zip, at a specific resolved commit SHA.

Two GitHub-hosted endpoints are used, both plain HTTP, no cloning:
  - api.github.com       -> resolve a branch/tag/ref to an exact commit SHA
  - codeload.github.com  -> download that exact commit as a .zip

Resolving to a SHA first (rather than just downloading the default branch's
zip) is what makes the commit-based history/caching in db.py possible: the
SHA is the identifier we dedupe on.
"""

import re

import httpx

from app.config import get_settings

_GITHUB_URL_RE = re.compile(
    r"github\.com[:/]+(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)"
    r"(?:\.git)?(?:/(?:tree|blob|commit)/(?P<ref>[^/]+))?/?$"
)


class GitHubError(RuntimeError):
    pass


def parse_github_url(url: str) -> tuple[str, str, str | None]:
    """Returns (owner, repo, ref). ref is None if the URL didn't specify a branch/tag/commit."""
    match = _GITHUB_URL_RE.search(url.strip())
    if not match:
        raise GitHubError(
            f"Not a recognizable GitHub repo URL: {url!r} "
            "(expected something like https://github.com/owner/repo)"
        )
    return match.group("owner"), match.group("repo"), match.group("ref")


def _headers() -> dict[str, str]:
    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-code-reviewer"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def resolve_commit_sha(owner: str, repo: str, ref: str | None) -> str:
    """Resolves a branch/tag/commit-ish ref (or the default branch, if ref is None)
    to an exact, full commit SHA."""
    settings = get_settings()
    timeout = settings.github_request_timeout_seconds
    async with httpx.AsyncClient(timeout=timeout, headers=_headers()) as client:
        if ref is None:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if resp.status_code == 404:
                raise GitHubError(f"Repo not found or private: {owner}/{repo}")
            resp.raise_for_status()
            ref = resp.json()["default_branch"]

        resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}")
        if resp.status_code == 404:
            raise GitHubError(f"Ref not found: {owner}/{repo}@{ref}")
        if resp.status_code == 403:
            raise GitHubError("GitHub API rate limit hit — set GITHUB_TOKEN to raise the limit")
        resp.raise_for_status()
        return resp.json()["sha"]


async def download_repo_zip(owner: str, repo: str, sha: str) -> bytes:
    """Downloads the exact commit as a zip. The zip always has one top-level
    directory named '{repo}-{sha}/' — see project_store.flatten_single_root."""
    url = f"https://codeload.github.com/{owner}/{repo}/zip/{sha}"
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise GitHubError(f"Could not download zip for {owner}/{repo}@{sha}")
        resp.raise_for_status()
        return resp.content
