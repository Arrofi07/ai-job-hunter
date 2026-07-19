"""
Slice 2 smoke test: proves both MCP servers are reachable and usable before
we build features on top of them.

Usage:
    uv run python -m scripts.mcp_smoke_test
    uv run python -m scripts.mcp_smoke_test --github-owner octocat --github-repo Hello-World

Note on the GitHub tool: confirmed against a real call to list_tools() (see
decisions log) — there's no dedicated "get repository metadata" tool in the
repos toolset at all, so FR9's file-based analysis (languages, frameworks,
CI/CD, Docker, tests) will work directly off `get_file_contents` /
`search_code` rather than a single repo-metadata call. This smoke test uses
get_file_contents on README.md, since that's the same capability FR9 will
actually lean on.
"""
import argparse
import asyncio
import json
import traceback

from app.mcp.client import extract_text
from app.mcp.gdrive_client import ensure_root_folder_structure, gdrive_mcp_session
from app.mcp.github_client import call_github_tool, github_mcp_session

# A well-known public repo, used only if you don't pass your own — this way
# the script runs without needing any of your own repos configured first.
# (octocat/Hello-World, an equally common choice, does NOT have a README.md
# — its readme file is literally named "README" with no extension, confirmed
# by checking raw.githubusercontent.com directly. Spoon-Knife does.)
DEFAULT_OWNER = "octocat"
DEFAULT_REPO = "Spoon-Knife"


def _print_full_error(e: BaseException) -> None:
    """anyio/asyncio TaskGroups wrap the real failure in an ExceptionGroup,
    which prints as a near-useless 'unhandled errors in a TaskGroup' unless
    you walk into .exceptions yourself. This unwraps it so the actual root
    cause (an HTTP error, a auth failure, whatever it is) is visible."""
    if isinstance(e, BaseExceptionGroup):
        for sub in e.exceptions:
            _print_full_error(sub)
    else:
        traceback.print_exception(type(e), e, e.__traceback__)


async def test_github(owner: str, repo: str) -> None:
    print("\n=== GitHub MCP ===")
    async with github_mcp_session() as session:
        tools = await session.list_tools()
        tool_names = sorted(t.name for t in tools.tools)
        print(f"Connected. {len(tool_names)} tools available:")
        for name in tool_names:
            print(f"  - {name}")

        result = await call_github_tool(
            session, "get_file_contents",
            {"owner": owner, "repo": repo, "path": "README.md"},
        )
        print(f"\nget_file_contents succeeded for {owner}/{repo}/README.md:")
        print(extract_text(result)[:1000])


async def test_gdrive() -> None:
    print("\n=== Google Drive MCP ===")
    async with gdrive_mcp_session() as session:
        tools = await session.list_tools()
        print(f"Connected. {len(tools.tools)} tools available: "
              f"{sorted(t.name for t in tools.tools)}")

        folder_ids = await ensure_root_folder_structure(session)
        print("\nFolder structure ensured:")
        print(json.dumps(folder_ids, indent=2))


async def main(owner: str, repo: str) -> None:
    try:
        await test_github(owner, repo)
    except BaseException as e:  # noqa: BLE001 - smoke test, surface everything
        print("\nGitHub MCP FAILED:")
        _print_full_error(e)

    try:
        await test_gdrive()
    except BaseException as e:  # noqa: BLE001
        print("\nGoogle Drive MCP FAILED:")
        _print_full_error(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-owner", default=DEFAULT_OWNER)
    parser.add_argument("--github-repo", default=DEFAULT_REPO)
    args = parser.parse_args()
    asyncio.run(main(args.github_owner, args.github_repo))