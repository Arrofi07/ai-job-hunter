from abc import ABC, abstractmethod


class LLMProviderClient(ABC):
    """Every provider (Gemini, Groq, Ollama, ...) implements this interface.

    Kept deliberately minimal for Slice 0 — just text in, text out. Structured
    output (JSON mode) and tool calling get added when a later slice actually
    needs them (resume extraction, matching), not speculatively now.
    """

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt, return the model's text response.

        Raises:
            LLMRateLimitError: provider signaled rate/quota limit.
            LLMConfigError: provider is misconfigured (e.g. missing API key).
            LLMError: any other provider failure.
        """
        raise NotImplementedError
