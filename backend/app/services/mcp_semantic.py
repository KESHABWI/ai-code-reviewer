"""Async wrapper around the cocoindex-code MCP server (cocoindex-io/cocoindex-code).

This is the semantic (embedding-based) alternative to mcp_index.py's grep/AST-based
code-index-mcp. Install it separately, it is not a Python dependency of this project:

    uv tool install --force "cocoindex-code[full]"

Key difference from code-index-mcp: cocoindex-code keeps a persistent on-disk index
under <project>/.cocoindex_code/, built by `ccc init` + `ccc index` before the MCP
server can search. code-index-mcp needs no such prep step. That's the real tradeoff
this module makes visible: semantic search costs an upfront indexing pass (which
downloads/runs an embedding model) in exchange for natural-language, cross-file
search instead of exact-text matching.

Every request and response is printed verbatim when settings.trace_io is enabled,
so you can see exactly what goes over the wire.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import get_settings


def _trace(arrow: str, label: str, payload) -> None:
    if not get_settings().trace_io:
        return
    print(f"\n{arrow} {label}")
    try:
        print(json.dumps(payload, indent=2, default=str)[:2000])
    except TypeError:
        print(str(payload)[:2000])


async def prepare_semantic_index(project_root: Path) -> str:
    """Run `ccc init -f` then `ccc index` once for a freshly uploaded project.

    Returns the combined stdout/stderr log (useful to surface to the caller/UI
    since this step can be slow and, on first run, downloads an embedding model).
    """
    log = []
    for args in (["ccc", "init", "-f"], ["ccc", "index"]):
        _trace("==>", f"subprocess: {' '.join(args)}", {"cwd": str(project_root)})
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(project_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        text = out.decode(errors="ignore")
        _trace("<==", f"subprocess result: {' '.join(args)}", text)
        log.append(f"$ {' '.join(args)}\n{text}")
    return "\n".join(log)


@asynccontextmanager
async def cocoindex_session(project_root: Path):
    """One MCP session against cocoindex-code, scoped to project_root via cwd."""
    params = StdioServerParameters(command="ccc", args=["mcp"], cwd=str(project_root))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        _trace("==>", "MCP initialize", {})
        init_result = await session.initialize()
        _trace("<==", "MCP initialize result", init_result.model_dump())
        yield session


async def semantic_search(project_root: Path, query: str, limit: int = 5) -> str:
    """Ask cocoindex-code for code related to `query`, by meaning, not exact text."""
    async with cocoindex_session(project_root) as session:
        args = {"query": query, "limit": limit}
        _trace("==>", "tools/call search", args)
        result = await session.call_tool("search", args)
        text = "\n".join(b.text for b in result.content if getattr(b, "type", None) == "text")
        _trace("<==", "tools/call search result", text)
        return text
