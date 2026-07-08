"""
These tests mock the provider classes entirely — they verify *routing and
fallback logic*, not real Gemini/Groq/Ollama connectivity. Real connectivity
should be checked manually once you have API keys: see the smoke test at the
bottom, skipped by default.
"""
from unittest.mock import MagicMock

import pytest

from app.config import LLMProvider, LLMTask, settings
from app.llm.client import LLMClient
from app.llm.exceptions import LLMRateLimitError


@pytest.fixture(autouse=True)
def reset_force_provider():
    original = settings.llm_force_provider
    yield
    settings.llm_force_provider = original


def _client_with_mocked_providers(monkeypatch, providers: dict[LLMProvider, MagicMock]):
    client = LLMClient()
    monkeypatch.setattr(client, "_get", lambda provider: providers[provider])
    return client


def test_routes_nuanced_task_to_configured_provider(monkeypatch):
    settings.llm_provider_nuanced = LLMProvider.GEMINI
    gemini = MagicMock()
    gemini.generate.return_value = "nuanced response"
    client = _client_with_mocked_providers(monkeypatch, {LLMProvider.GEMINI: gemini})

    result = client.generate(LLMTask.NUANCED, "write a cover letter paragraph")

    assert result == "nuanced response"
    gemini.generate.assert_called_once_with("write a cover letter paragraph", system=None)


def test_routes_structured_task_to_configured_provider(monkeypatch):
    settings.llm_provider_structured = LLMProvider.GROQ
    groq = MagicMock()
    groq.generate.return_value = "structured response"
    client = _client_with_mocked_providers(monkeypatch, {LLMProvider.GROQ: groq})

    result = client.generate(LLMTask.STRUCTURED, "extract skills from resume")

    assert result == "structured response"


def test_force_provider_overrides_task_routing(monkeypatch):
    settings.llm_force_provider = LLMProvider.OLLAMA
    ollama = MagicMock()
    ollama.generate.return_value = "forced response"
    client = _client_with_mocked_providers(monkeypatch, {LLMProvider.OLLAMA: ollama})

    result = client.generate(LLMTask.NUANCED, "anything")

    assert result == "forced response"


def test_falls_back_on_rate_limit(monkeypatch):
    settings.llm_provider_nuanced = LLMProvider.GEMINI
    settings.llm_fallback_provider = LLMProvider.OLLAMA

    gemini = MagicMock()
    gemini.generate.side_effect = LLMRateLimitError("quota exceeded")
    ollama = MagicMock()
    ollama.generate.return_value = "fallback response"

    client = _client_with_mocked_providers(
        monkeypatch, {LLMProvider.GEMINI: gemini, LLMProvider.OLLAMA: ollama}
    )

    result = client.generate(LLMTask.NUANCED, "prompt")

    assert result == "fallback response"
    ollama.generate.assert_called_once()


def test_does_not_fall_back_on_non_rate_limit_errors(monkeypatch):
    settings.llm_provider_nuanced = LLMProvider.GEMINI
    gemini = MagicMock()
    gemini.generate.side_effect = ValueError("bad request")

    client = _client_with_mocked_providers(monkeypatch, {LLMProvider.GEMINI: gemini})

    with pytest.raises(ValueError):
        client.generate(LLMTask.NUANCED, "prompt")


@pytest.mark.skipif(reason="Requires real API keys in .env — run manually, not in CI")
def test_live_smoke_gemini():
    from app.llm.gemini_provider import GeminiProvider

    provider = GeminiProvider()
    result = provider.generate("Say 'hello' and nothing else.")
    assert result.strip()


@pytest.mark.skipif(reason="Requires real API keys in .env — run manually, not in CI")
def test_live_smoke_groq():
    from app.llm.groq_provider import GroqProvider

    provider = GroqProvider()
    result = provider.generate("Say 'hello' and nothing else.")
    assert result.strip()
