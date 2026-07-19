"""
Diagnostic, not a permanent part of the app: checks exactly which scopes
the current access token carries, via Google's tokeninfo endpoint. Exists
because "The caller does not have permission" from search_files is
ambiguous — it could mean the token only effectively has drive.file (not
drive.readonly), or something else entirely. This tells us for certain
rather than guessing at a third fix in a row.

Usage:
    uv run python -m scripts.gdrive_token_debug
"""
import sys

import httpx

from app.mcp.gdrive_auth import get_access_token


def main() -> None:
    print("Starting token debug check...", flush=True)
    try:
        token = get_access_token()
        print(f"Got access token (first 20 chars): {token[:20]}...", flush=True)
    except Exception:
        print("Failed to get access token:", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    try:
        resp = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"access_token": token}
        )
        print(f"Status: {resp.status_code}", flush=True)
        print(resp.json(), flush=True)
    except Exception:
        print("Request to tokeninfo failed:", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()