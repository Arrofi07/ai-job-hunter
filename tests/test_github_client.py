import pytest

from app.config import settings
from app.mcp.github_client import GitHubMCPConfigError, _headers


@pytest.fixture(autouse=True)
def reset_pat():
    original = settings.github_mcp_pat
    yield
    settings.github_mcp_pat = original


def test_raises_config_error_when_pat_missing():
    settings.github_mcp_pat = None
    with pytest.raises(GitHubMCPConfigError):
        _headers()


def test_headers_always_include_readonly_true():
    settings.github_mcp_pat = "fake-pat"
    headers = _headers()

    assert headers["X-MCP-Readonly"] == "true"
    assert headers["Authorization"] == "Bearer fake-pat"


def test_readonly_is_not_configurable_via_settings():
    """Regression guard for the design intent in the module docstring: even
    if something in the codebase tried to read a 'readonly' setting and
    pass False, there's no such setting to read — X-MCP-Readonly is a
    literal in the code, not sourced from config."""
    import inspect

    from app.mcp import github_client

    source = inspect.getsource(github_client._headers)
    assert '"X-MCP-Readonly": "true"' in source