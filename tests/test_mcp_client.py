from unittest.mock import AsyncMock

import pytest
from mcp.types import CallToolResult, TextContent

from app.mcp.client import MCPToolError, call_tool, extract_text


def _text_result(text: str, is_error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], isError=is_error)


@pytest.mark.asyncio
async def test_call_tool_returns_result_on_success():
    session = AsyncMock()
    session.call_tool.return_value = _text_result("ok")

    result = await call_tool(session, "some_tool", {"a": 1})

    assert extract_text(result) == "ok"
    session.call_tool.assert_awaited_once_with("some_tool", {"a": 1})


@pytest.mark.asyncio
async def test_call_tool_raises_on_is_error():
    session = AsyncMock()
    session.call_tool.return_value = _text_result("something broke", is_error=True)

    with pytest.raises(MCPToolError, match="something broke"):
        await call_tool(session, "some_tool", {})


def test_extract_text_joins_multiple_blocks():
    result = CallToolResult(
        content=[
            TextContent(type="text", text="first"),
            TextContent(type="text", text="second"),
        ],
        isError=False,
    )
    assert extract_text(result) == "first\nsecond"