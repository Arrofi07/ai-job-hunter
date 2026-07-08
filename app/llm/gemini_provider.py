from app.config import settings
from app.llm.base import LLMProviderClient
from app.llm.exceptions import LLMConfigError, LLMError, LLMRateLimitError


class GeminiProvider(LLMProviderClient):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise LLMConfigError("GEMINI_API_KEY is not set")
        # Imported lazily so importing this module doesn't require the
        # google-genai package unless Gemini is actually selected.
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        from google.genai import errors as genai_errors

        config = {"system_instruction": system} if system else {}
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except genai_errors.ClientError as e:
            if getattr(e, "code", None) == 429:
                raise LLMRateLimitError(str(e)) from e
            raise LLMError(str(e)) from e

        if not response.text:
            raise LLMError("Gemini returned an empty response")
        return response.text
