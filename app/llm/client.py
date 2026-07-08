import logging

from app.config import LLMProvider, LLMTask, settings
from app.llm.base import LLMProviderClient
from app.llm.exceptions import LLMRateLimitError

logger = logging.getLogger(__name__)

_PROVIDER_CLASSES: dict[LLMProvider, type[LLMProviderClient]] = {}


def _load_provider_classes() -> None:
    # Imported lazily so a missing optional dependency (e.g. no groq installed)
    # doesn't break importing this module — only breaks actually using that provider.
    if _PROVIDER_CLASSES:
        return
    from app.llm.gemini_provider import GeminiProvider
    from app.llm.groq_provider import GroqProvider
    from app.llm.ollama_provider import OllamaProvider

    _PROVIDER_CLASSES.update(
        {
            LLMProvider.GEMINI: GeminiProvider,
            LLMProvider.GROQ: GroqProvider,
            LLMProvider.OLLAMA: OllamaProvider,
        }
    )


def _instantiate(provider: LLMProvider) -> LLMProviderClient:
    _load_provider_classes()
    return _PROVIDER_CLASSES[provider]()


class LLMClient:
    """
    Single entry point the rest of the app uses to talk to an LLM.

    Usage:
        client = LLMClient()
        text = client.generate(LLMTask.STRUCTURED, prompt="...", system="...")

    Routing:
        - `llm_force_provider` (if set) wins for every task — flip this in .env
          when a provider is rate-limited, no code changes needed.
        - Otherwise each LLMTask routes to its configured provider
          (see Settings.llm_provider_nuanced / llm_provider_structured).
        - If the chosen provider raises LLMRateLimitError, we retry once
          against `llm_fallback_provider` and log a warning. We do not retry
          on other error types — those usually mean a bad request, and
          retrying elsewhere just repeats the same mistake against a
          different provider.
    """

    def __init__(self) -> None:
        self._instances: dict[LLMProvider, LLMProviderClient] = {}

    def _get(self, provider: LLMProvider) -> LLMProviderClient:
        if provider not in self._instances:
            self._instances[provider] = _instantiate(provider)
        return self._instances[provider]

    def _provider_for_task(self, task: LLMTask) -> LLMProvider:
        if settings.llm_force_provider is not None:
            return settings.llm_force_provider
        if task == LLMTask.NUANCED:
            return settings.llm_provider_nuanced
        return settings.llm_provider_structured

    def generate(self, task: LLMTask, prompt: str, system: str | None = None) -> str:
        primary = self._provider_for_task(task)
        try:
            return self._get(primary).generate(prompt, system=system)
        except LLMRateLimitError:
            fallback = settings.llm_fallback_provider
            if fallback == primary:
                raise
            logger.warning(
                "Provider %s rate-limited on task %s; falling back to %s",
                primary, task, fallback,
            )
            return self._get(fallback).generate(prompt, system=system)
