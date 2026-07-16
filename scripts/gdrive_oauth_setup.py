"""
One-time setup: obtains the initial Google OAuth token via a browser consent
flow, then saves it so app/mcp/gdrive_auth.py can silently refresh it from
then on.

Prerequisites (see SETUP.md for the full walkthrough):
  1. A Google Cloud project with the Drive API enabled.
  2. An OAuth consent screen configured (Internal or External).
  3. An OAuth 2.0 Client ID of type "Desktop app", downloaded as JSON.
  4. GDRIVE_OAUTH_CLIENT_ID and GDRIVE_OAUTH_CLIENT_SECRET set in .env
     (from that downloaded JSON's `client_id` / `client_secret` fields).

Usage:
    uv run python -m scripts.gdrive_oauth_setup

This opens your default browser for you to sign in and grant access. After
you approve, the token is saved to the path in GDRIVE_TOKEN_PATH (default
`.gdrive_token.json`) — add that path to .gitignore, it's a secret.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import settings
from app.mcp.gdrive_auth import DRIVE_SCOPES, save_token_file


def main() -> None:
    if not settings.gdrive_oauth_client_id or not settings.gdrive_oauth_client_secret:
        raise SystemExit(
            "GDRIVE_OAUTH_CLIENT_ID and GDRIVE_OAUTH_CLIENT_SECRET must be set "
            "in .env before running this. See SETUP.md for how to get these "
            "from Google Cloud Console."
        )

    client_config = {
        "installed": {
            "client_id": settings.gdrive_oauth_client_id,
            "client_secret": settings.gdrive_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, DRIVE_SCOPES)
    creds = flow.run_local_server(port=0)

    save_token_file(creds)
    print(f"Token saved to {settings.gdrive_token_path}. You're set for Google Drive MCP access.")


if __name__ == "__main__":
    main()