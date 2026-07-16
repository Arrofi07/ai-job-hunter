"""
Slice 2 smoke test: proves both MCP servers are reachable and usable before
we build features on top of them.

Usage:
    uv run python -m scripts.mcp_smoke_test
    uv run python -m scripts.mcp_smoke_test --github-owner octocat --github-repo Hello-World

Note on the GitHub tool call: I confirmed the server URL, transport, and
auth headers against GitHub's official docs, but not the *exact* tool name
for "get repository info" — GitHub doesn't publish a full tool-name
reference the way Google does for Drive. This script lists all available
tools first specifically so that if the guessed tool name is wrong, you get
the real tool list to report back rather than just a bare failure.
"""
import argparse
import asyncio
import json

from app.mcp.client import extract_text
from app.mcp.gdrive_client import ensure_root_folder_structure, gdrive_mcp_session
from app.mcp.github_client import call_github_tool, github_mcp_session

# A well-known public repo, used only if you don't pass your own — this way
# the script runs without needing any of your own repos configured first.
DEFAULT_OWNER = "octocat"
DEFAULT_REPO = "Hello-World"

# Tool name guesses, tried in order, for "get repository metadata" — the
# first one that exists and succeeds is used. If none work, the full tool
# list (printed regardless) tells us the real name to hardcode instead.
REPO_INFO_TOOL_CANDIDATES = ["get_repository", "get_repo", "repository_get"]


async def test_github(owner: str, repo: str) -> None:
    print("\n=== GitHub MCP ===")
    async with github_mcp_session() as session:
        tools = await session.list_tools()
        tool_names = sorted(t.name for t in tools.tools)
        print(f"Connected. {len(tool_names)} tools available:")
        for name in tool_names:
            print(f"  - {name}")

        for candidate in REPO_INFO_TOOL_CANDIDATES:
            if candidate not in tool_names:
                continue
            try:
                result = await call_github_tool(
                    session, candidate, {"owner": owner, "repo": repo}
                )
                print(f"\n'{candidate}' succeeded for {owner}/{repo}:")
                print(extract_text(result)[:1000])
                return
            except Exception as e:  # noqa: BLE001 - smoke test, want to see any failure
                print(f"\n'{candidate}' exists but failed: {e}")

        print(
            "\nNone of the guessed repo-info tool names worked. See the tool "
            "list above for the real name, then tell me which one it is."
        )


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
    except Exception as e:  # noqa: BLE001 - smoke test, surface everything
        print(f"\nGitHub MCP FAILED: {e}")

    try:
        await test_gdrive()
    except Exception as e:  # noqa: BLE001
        print(f"\nGoogle Drive MCP FAILED: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-owner", default=DEFAULT_OWNER)
    parser.add_argument("--github-repo", default=DEFAULT_REPO)
    args = parser.parse_args()
    asyncio.run(main(args.github_owner, args.github_repo))