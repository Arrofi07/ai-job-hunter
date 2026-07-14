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
        except genai_errors.APIError as e:
            # 429 = quota/rate limit. 5xx (ServerError) = Google's side is
            # down/overloaded ("high demand", 503 UNAVAILABLE, etc.) — from
            # the caller's perspective both mean "Gemini isn't answering
            # right now, try the fallback provider," so both route through
            # LLMRateLimitError rather than only the literal 429 case.
            if e.code == 429 or e.code >= 500:
                raise LLMRateLimitError(str(e)) from e
            raise LLMError(str(e)) from e

        if not response.text:
            raise LLMError("Gemini returned an empty response")
        return response.text
