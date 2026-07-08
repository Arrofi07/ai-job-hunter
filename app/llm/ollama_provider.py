import httpx

from app.config import settings
from app.llm.base import LLMProviderClient
from app.llm.exceptions import LLMError

# Ollama runs locally with no quota, so there's no rate-limit path to handle —
# it's the deliberate escape hatch when Gemini/Groq are throttled. Its
# tradeoff is quality/speed depending on your machine, not availability.


class OllamaProvider(LLMProviderClient):
    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            resp = httpx.post(f"{self._base_url}/api/generate", json=payload, timeout=120)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMError(
                f"Ollama request failed ({e}). Is `ollama serve` running at {self._base_url}?"
            ) from e

        data = resp.json()
        content = data.get("response")
        if not content:
            raise LLMError("Ollama returned an empty response")
        return content
