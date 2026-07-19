"""
Loads and refreshes the Google OAuth token saved by
scripts/gdrive_oauth_setup.py. That script is the one-time interactive step
(opens a browser for consent) — this module is what runs on every request
afterward, refreshing the access token from the stored refresh token as
needed, with no user interaction.

Scope: Google's own docs for the Drive MCP server specify exactly
`drive.readonly` + `drive.file` — not the broader `drive` scope. This combo
actually covers FR6's needs correctly: `drive.readonly` reads files that
already exist in the person's Drive (their resume, their cover letter
template), `drive.file` creates/manages files this app creates (job
folders, generated cover letters, reports). It's more correctly scoped than
a blanket `drive` grant, not less capable for what we actually need.
"""
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.config import settings

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


class GDriveAuthError(Exception):
    pass


def _load_token_file() -> dict:
    if not os.path.exists(settings.gdrive_token_path):
        raise GDriveAuthError(
            f"No token file found at {settings.gdrive_token_path}. "
            "Run `uv run python -m scripts.gdrive_oauth_setup` first — "
            "this is a one-time step that opens a browser for you to grant access."
        )
    with open(settings.gdrive_token_path) as f:
        return json.load(f)


def get_access_token() -> str:
    """Returns a valid access token, refreshing it first if it's expired.
    This is what gdrive_client.py calls before every MCP request — access
    tokens are short-lived (~1hr), so assume it needs refreshing rather than
    caching it across calls."""
    token_data = _load_token_file()

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gdrive_oauth_client_id,
        client_secret=settings.gdrive_oauth_client_secret,
        scopes=DRIVE_SCOPES,
    )

    if not creds.valid:
        if not creds.refresh_token:
            raise GDriveAuthError(
                "Stored credentials have no refresh token and can't be "
                "renewed. Re-run scripts/gdrive_oauth_setup.py."
            )
        creds.refresh(Request())
        save_token_file(creds)

    return creds.token


def save_token_file(creds: Credentials) -> None:
    with open(settings.gdrive_token_path, "w") as f:
        json.dump(
            {"token": creds.token, "refresh_token": creds.refresh_token},
            f,
        )