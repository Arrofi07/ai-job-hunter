"""
Regression tests for the bug found running against real Gemini traffic:
a 503 'high demand' ServerError wasn't caught (only 429 ClientError was),
so it crashed instead of triggering fallback to Groq/Ollama. Fixed by
treating 5xx and connection-level errors the same as 429 — both mean
"this provider isn't answering, use the fallback."

These construct real SDK exception objects (not just generic mocks) so the
test actually exercises our except-clause matching against the real
exception hierarchy, not an assumption about it.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.llm.exceptions import LLMConfigError, LLMError, LLMRateLimitError


@pytest.fixture(autouse=True)
def fake_api_keys(monkeypatch):
    monkeypatch.setattr("app.config.settings.gemini_api_key", "fake-key")
    monkeypatch.setattr("app.config.settings.groq_api_key", "fake-key")


class TestGeminiErrorHandling:
    def _make_provider(self):
        from app.llm.gemini_provider import GeminiProvider

        with patch("google.genai.Client"):
            return GeminiProvider()

    def test_503_server_error_triggers_rate_limit_fallback_path(self):
        from google.genai import errors as genai_errors

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 503
        error = genai_errors.ServerError(
            503, {"error": {"message": "high demand", "status": "UNAVAILABLE"}}, response
        )
        provider._client.models.generate_content.side_effect = error

        with pytest.raises(LLMRateLimitError):
            provider.generate("prompt")

    def test_429_client_error_triggers_rate_limit_fallback_path(self):
        from google.genai import errors as genai_errors

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 429
        error = genai_errors.ClientError(
            429, {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}}, response
        )
        provider._client.models.generate_content.side_effect = error

        with pytest.raises(LLMRateLimitError):
            provider.generate("prompt")

    def test_400_bad_request_does_not_trigger_fallback(self):
        from google.genai import errors as genai_errors

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 400
        error = genai_errors.ClientError(
            400, {"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}}, response
        )
        provider._client.models.generate_content.side_effect = error

        with pytest.raises(LLMError) as exc_info:
            provider.generate("prompt")
        assert not isinstance(exc_info.value, LLMRateLimitError)


class TestGroqErrorHandling:
    def _make_provider(self):
        from app.llm.groq_provider import GroqProvider

        with patch("groq.Groq"):
            return GroqProvider()

    def test_internal_server_error_triggers_rate_limit_fallback_path(self):
        import groq

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 500
        error = groq.InternalServerError("server error", response=response, body=None)
        provider._client.chat.completions.create.side_effect = error

        with pytest.raises(LLMRateLimitError):
            provider.generate("prompt")

    def test_rate_limit_error_triggers_fallback_path(self):
        import groq

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 429
        error = groq.RateLimitError("rate limited", response=response, body=None)
        provider._client.chat.completions.create.side_effect = error

        with pytest.raises(LLMRateLimitError):
            provider.generate("prompt")

    def test_connection_error_triggers_fallback_path(self):
        import httpx
        from groq import APIConnectionError

        provider = self._make_provider()
        error = APIConnectionError(request=MagicMock(spec=httpx.Request))
        provider._client.chat.completions.create.side_effect = error

        with pytest.raises(LLMRateLimitError):
            provider.generate("prompt")

    def test_bad_request_does_not_trigger_fallback(self):
        import groq

        provider = self._make_provider()
        response = MagicMock()
        response.status_code = 400
        error = groq.BadRequestError("bad request", response=response, body=None)
        provider._client.chat.completions.create.side_effect = error

        with pytest.raises(LLMError) as exc_info:
            provider.generate("prompt")
        assert not isinstance(exc_info.value, LLMRateLimitError)
