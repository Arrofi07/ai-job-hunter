import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from app.mcp.client import MCPToolError
from app.mcp.gdrive_client import (
    SUBFOLDERS,
    _create_folder,
    _find_folder,
    ensure_root_folder_structure,
)


def _tool_result(payload) -> CallToolResult:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return CallToolResult(content=[TextContent(type="text", text=text)], isError=False)


class TestFindFolder:
    @pytest.mark.asyncio
    async def test_returns_id_when_folder_found(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result({"files": [{"id": "folder-123"}]})),
        ):
            result = await _find_folder(session, "Resume", parent_id="root-id")

        assert result == "folder-123"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_files_key(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result({"files": []})),
        ):
            result = await _find_folder(session, "Resume", parent_id="root-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result("")),
        ):
            result = await _find_folder(session, "Resume", parent_id="root-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_unparseable_response_rather_than_crashing(self):
        """If the real response format turns out not to be JSON (an
        assumption we flagged as unverified), degrade to 'not found' —
        worst case we try to create a folder that already exists, which
        Drive will just make a duplicate of, rather than crashing the
        whole bootstrap."""
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result("Found 1 folder named Resume")),
        ):
            result = await _find_folder(session, "Resume", parent_id="root-id")

        assert result is None


class TestCreateFolder:
    @pytest.mark.asyncio
    async def test_returns_id_from_json_response(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result({"id": "new-folder-456"})),
        ):
            result = await _create_folder(session, "Resume", parent_id="root-id")

        assert result == "new-folder-456"

    @pytest.mark.asyncio
    async def test_raises_clear_error_on_unexpected_response_shape(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client.call_gdrive_tool",
            new=AsyncMock(return_value=_tool_result("Created folder successfully")),
        ):
            with pytest.raises(MCPToolError, match="didn't match the expected shape"):
                await _create_folder(session, "Resume", parent_id="root-id")


class TestEnsureRootFolderStructure:
    @pytest.mark.asyncio
    async def test_creates_root_and_all_subfolders_when_none_exist(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client._find_folder", new=AsyncMock(return_value=None)
        ), patch(
            "app.mcp.gdrive_client._create_folder",
            new=AsyncMock(side_effect=lambda s, name, parent_id: f"id-{name}"),
        ) as mock_create:
            result = await ensure_root_folder_structure(session)

        assert result["AI Job Hunter"] == "id-AI Job Hunter"
        for sub in SUBFOLDERS:
            assert result[sub] == f"id-{sub}"
        # root + 4 subfolders = 5 creations
        assert mock_create.await_count == 5

    @pytest.mark.asyncio
    async def test_skips_creation_when_everything_already_exists(self):
        session = AsyncMock()
        with patch(
            "app.mcp.gdrive_client._find_folder",
            new=AsyncMock(side_effect=lambda s, name, parent_id: f"existing-{name}"),
        ), patch("app.mcp.gdrive_client._create_folder") as mock_create:
            result = await ensure_root_folder_structure(session)

        assert result["AI Job Hunter"] == "existing-AI Job Hunter"
        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_only_missing_subfolder(self):
        """Resume already exists, everything else doesn't — only the
        missing ones get created."""
        session = AsyncMock()

        async def fake_find(s, name, parent_id):
            return "existing-id" if name in ("AI Job Hunter", "Resume") else None

        with patch("app.mcp.gdrive_client._find_folder", new=fake_find), patch(
            "app.mcp.gdrive_client._create_folder",
            new=AsyncMock(side_effect=lambda s, name, parent_id: f"created-{name}"),
        ) as mock_create:
            result = await ensure_root_folder_structure(session)

        assert result["Resume"] == "existing-id"
        assert result["Templates"] == "created-Templates"
        assert mock_create.await_count == 3  # Templates, Jobs, Reports