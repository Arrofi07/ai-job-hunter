from app.config import settings
from app.llm.base import LLMProviderClient
from app.llm.exceptions import LLMConfigError, LLMError, LLMRateLimitError


class GroqProvider(LLMProviderClient):
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise LLMConfigError("GROQ_API_KEY is not set")
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        from groq import APIStatusError

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except APIStatusError as e:
            if e.status_code == 429:
                raise LLMRateLimitError(str(e)) from e
            raise LLMError(str(e)) from e

        content = response.choices[0].message.content
        if not content:
            raise LLMError("Groq returned an empty response")
        return content
