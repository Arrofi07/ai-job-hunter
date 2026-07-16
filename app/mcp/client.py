"""
Thin wrapper over the official `mcp` Python SDK's Streamable HTTP transport.
Both GitHub MCP and Google Drive MCP are remote servers speaking this same
transport, so one generic client covers both — see github_client.py and
gdrive_client.py for the server-specific configuration (URL, auth headers).

Deliberately minimal for Slice 2: connect, list tools, call a tool. No
retry/backoff here yet — that's the same class of resilience work we did
for the LLM providers (Slice 0), and worth doing once we know which MCP
failure modes actually show up in practice, rather than guessing now.
"""
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult


class MCPToolError(Exception):
    """Raised when a tool call completes but reports isError=True, or when
    the server itself rejects the request (e.g. 401 from a bad/expired token)."""


@asynccontextmanager
async def mcp_session(url: str, headers: dict[str, str]):
    """Usage:
        async with mcp_session(url, headers) as session:
            tools = await session.list_tools()
            result = await call_tool(session, "some_tool", {...})
    """
    async with streamablehttp_client(url, headers=headers) as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_tool(session: ClientSession, name: str, arguments: dict) -> CallToolResult:
    result = await session.call_tool(name, arguments)
    if result.isError:
        error_text = _extract_text(result)
        raise MCPToolError(f"Tool '{name}' returned an error: {error_text}")
    return result


def _extract_text(result: CallToolResult) -> str:
    """Most tool responses are a list of content blocks; the common case is
    a single TextContent block. Joining all text blocks covers multi-block
    responses without assuming there's exactly one."""
    texts = [block.text for block in result.content if hasattr(block, "text")]
    return "\n".join(texts)


def extract_text(result: CallToolResult) -> str:
    return _extract_text(result)