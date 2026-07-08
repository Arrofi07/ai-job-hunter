"""
Central configuration, loaded from environment variables / .env.

Keep this the single place that reads os.environ — nothing else in the app
should call os.getenv directly, so we always know where config comes from.
"""
from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    GEMINI = "gemini"
    GROQ = "groq"
    OLLAMA = "ollama"


class LLMTask(StrEnum):
    """
    Different pipeline steps have different needs (nuance & long context vs.
    cheap structured extraction). We route per-task rather than one provider
    for everything, so a rate limit on one provider doesn't stall the whole
    pipeline.
    """
    NUANCED = "nuanced"       # matching explanations, cover letter body
    STRUCTURED = "structured"  # resume parsing, classification, extraction


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM provider routing ---
    # Which provider handles each task by default.
    llm_provider_nuanced: LLMProvider = LLMProvider.GEMINI
    llm_provider_structured: LLMProvider = LLMProvider.GROQ

    # If a provider errors or rate-limits, fall back to this one for *all* tasks.
    # Set this to OLLAMA if you're hitting Gemini free-tier limits and want a
    # local, unlimited (but slower/lower-quality) escape hatch.
    llm_fallback_provider: LLMProvider = LLMProvider.OLLAMA

    # Escape hatch: force everything onto a single provider regardless of task,
    # e.g. during Gemini rate-limit windows. None = use per-task routing above.
    llm_force_provider: LLMProvider | None = None

    # --- Provider credentials / endpoints ---
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # --- Storage ---
    database_url: str = "postgresql+psycopg2://jobhunter:jobhunter@localhost:5432/jobhunter"
    qdrant_url: str = "http://localhost:6333"

    # --- Google Drive / GitHub MCP (filled in during Slice 2) ---
    gdrive_root_folder_name: str = "AI Job Hunter"


settings = Settings()
