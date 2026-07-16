"""
GitHub MCP client. Read-only is not a configurable option here — it's
hardcoded — because FR9 says the GitHub MCP integration must never modify
repositories. Making that a settings toggle would let a future bug (or a
copy-pasted config from somewhere else) silently turn write access back on.
"""
from mcp.types import CallToolResult

from app.config import settings
from app.mcp.client import call_tool, mcp_session


class GitHubMCPConfigError(Exception):
    pass


def _headers() -> dict[str, str]:
    if not settings.github_mcp_pat:
        raise GitHubMCPConfigError(
            "GITHUB_MCP_PAT is not set. Create a fine-grained personal access "
            "token scoped to read-only repository access and set it in .env."
        )
    return {
        "Authorization": f"Bearer {settings.github_mcp_pat}",
        "X-MCP-Readonly": "true",  # hardcoded, not derived from settings — see module docstring
        "X-MCP-Toolsets": settings.github_mcp_toolsets,
    }


def github_mcp_session():
    """Usage:
        async with github_mcp_session() as session:
            result = await call_github_tool(session, "some_tool", {...})
    """
    return mcp_session(settings.github_mcp_url, headers=_headers())


async def call_github_tool(session, name: str, arguments: dict) -> CallToolResult:
    return await call_tool(session, name, arguments)