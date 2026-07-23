"""Async wrapper around the code-index-mcp MCP server (johnhuang316/code-index-mcp).

We spawn it over stdio via `uvx code-index-mcp` and keep ONE session open per
project-review operation, reusing it across many `analyze_file` calls instead
of respawning the server per file.
"""

import json
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def code_index_session(project_path: str):
    params = StdioServerParameters(command="uvx", args=["code-index-mcp"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        _trace("==>", "MCP initialize", {})
        init_result = await session.initialize()
        _trace("<==", "MCP initialize result", init_result.model_dump())
        _trace("==>", "tools/call set_project_path", {"path": project_path})
        await session.call_tool("set_project_path", {"path": project_path})
        yield session


def extract_text(result) -> str:
    """Pull the plain-text content out of an MCP CallToolResult."""
    parts = [
        block.text
        for block in getattr(result, "content", [])
        if getattr(block, "type", None) == "text"
    ]
    return "\n".join(parts)
