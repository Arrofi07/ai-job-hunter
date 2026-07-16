"""
Google Drive MCP client, plus the FR5 folder-structure bootstrap:

    AI Job Hunter/
        Resume/
        Templates/
        Jobs/
        Reports/

Important constraint from the actual tool list (verified against Google's
MCP reference, not assumed): there is no dedicated "list folder" or "create
folder" tool. Folders are just Drive files with mimeType
`application/vnd.google-apps.folder`, so:
  - finding a folder = `search_files` with a `title = '...' and mimeType = '...'
    and parentId = '...'` query
  - creating a folder = `create_file` with that same mimeType, no content
"""
import json

from app.config import settings
from app.mcp.client import MCPToolError, call_tool, extract_text, mcp_session
from app.mcp.gdrive_auth import get_access_token

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
SUBFOLDERS = ["Resume", "Templates", "Jobs", "Reports"]


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_access_token()}"}


def gdrive_mcp_session():
    """Usage:
        async with gdrive_mcp_session() as session:
            result = await call_gdrive_tool(session, "search_files", {...})
    """
    return mcp_session(settings.gdrive_mcp_url, headers=_headers())


async def call_gdrive_tool(session, name: str, arguments: dict):
    return await call_tool(session, name, arguments)


async def _find_folder(session, name: str, parent_id: str | None) -> str | None:
    """Returns the folder's file ID if it exists directly under parent_id
    (or in 'My Drive' root if parent_id is None), else None."""
    query = f"title = '{name}' and mimeType = '{FOLDER_MIME_TYPE}'"
    query += f" and parentId = '{parent_id}'" if parent_id else " and parentId = 'root'"

    result = await call_gdrive_tool(session, "search_files", {"query": query})
    text = extract_text(result)
    if not text or text.strip() == "":
        return None

    # search_files returns a natural-language/text listing per the tool's
    # description, not guaranteed JSON — but Google's docs example responses
    # are JSON-shaped, so try that first and fall back to "not found" rather
    # than guessing at a text-parsing scheme we haven't verified.
    try:
        data = json.loads(text)
        files = data.get("files", data if isinstance(data, list) else [])
        return files[0]["id"] if files else None
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


async def _create_folder(session, name: str, parent_id: str | None) -> str:
    args = {
        "name": name,
        "mimeType": FOLDER_MIME_TYPE,
    }
    if parent_id:
        args["parents"] = [parent_id]

    result = await call_gdrive_tool(session, "create_file", args)
    text = extract_text(result)
    try:
        data = json.loads(text)
        return data["id"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # This response-shape assumption (JSON with an "id" field) is based
        # on Google's documented tool description, not a live call we could
        # verify from this environment — if this fires, the real response
        # text is in the exception, and that's exactly what to paste back
        # for a fix, same as any other live-testing gap in this project.
        raise MCPToolError(
            f"create_file response didn't match the expected shape. "
            f"Raw response: {text[:500]}"
        ) from e


async def ensure_root_folder_structure(session) -> dict[str, str]:
    """Creates AI Job Hunter/{Resume,Templates,Jobs,Reports} if any part is
    missing, returns {folder_name: file_id} for the root and all subfolders.
    Idempotent — safe to call on every app startup once wired in later."""
    root_name = settings.gdrive_root_folder_name

    root_id = await _find_folder(session, root_name, parent_id=None)
    if root_id is None:
        root_id = await _create_folder(session, root_name, parent_id=None)

    folder_ids = {root_name: root_id}
    for sub in SUBFOLDERS:
        sub_id = await _find_folder(session, sub, parent_id=root_id)
        if sub_id is None:
            sub_id = await _create_folder(session, sub, parent_id=root_id)
        folder_ids[sub] = sub_id

    return folder_ids