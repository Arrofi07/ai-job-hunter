"""
Central configuration, loaded from environment variables / .env.

Keep this the single place that reads os.environ — nothing else in the app
should call os.getenv directly, so we always know where config comes from.
"""
from enum import StrEnum

from pydantic import field_validator
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
    # NOTE: Gemini free tier is only 20 requests/day for gemini-2.5-flash —
    # exhausted almost immediately once daily job search + matching + cover
    # letters are all running. Defaulting nuanced tasks to Ollama (free,
    # unlimited, runs locally) until Gemini billing is set up. Switch this
    # back to LLMProvider.GEMINI once that's in place, if quality matters
    # more than cost for cover letters specifically.
    llm_provider_nuanced: LLMProvider = LLMProvider.OLLAMA
    llm_provider_structured: LLMProvider = LLMProvider.GROQ

    # If a provider errors or rate-limits, fall back to this one for *all* tasks.
    # Now that Ollama is the default *primary* for nuanced tasks (see above),
    # falling back to Ollama-on-Ollama-failure would be a no-op — the client
    # skips fallback when primary == fallback. Gemini as the fallback target
    # means: normal case costs nothing (Ollama), and if Ollama itself is down
    # (not running, wrong model pulled, etc.) you still get a real answer
    # instead of a hard failure, using a sliver of your daily Gemini quota.
    llm_fallback_provider: LLMProvider = LLMProvider.GEMINI

    # Escape hatch: force everything onto a single provider regardless of task,
    # e.g. during Gemini rate-limit windows. None = use per-task routing above.
    llm_force_provider: LLMProvider | None = None

    @field_validator("llm_force_provider", mode="before")
    @classmethod
    def _blank_env_means_unset(cls, v):
        # .env.example ships this as `LLM_FORCE_PROVIDER=` (blank) so people
        # can see the option without setting it. pydantic-settings treats a
        # blank env value as the literal string "", not "unset" — which fails
        # enum validation. Treat blank/whitespace as None instead.
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

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

    # --- Google Drive / GitHub MCP (Slice 2) ---
    gdrive_root_folder_name: str = "AI Job Hunter"

    # GitHub MCP (official remote server: https://github.com/github/github-mcp-server)
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    github_mcp_pat: str | None = None
    # Kept read-only always, per FR9: "never modifies repositories." This
    # isn't just a default the person can quietly change — see github_client.py.
    github_mcp_toolsets: str = "context,repos"  # minimal: identity check + repo intelligence for portfolio analysis

    # Google Drive MCP (official remote server: https://developers.google.com/workspace/drive/api/guides/configure-mcp-server)
    gdrive_mcp_url: str = "https://drivemcp.googleapis.com/mcp/v1"
    gdrive_oauth_client_id: str | None = None
    gdrive_oauth_client_secret: str | None = None
    # Where the OAuth refresh token lives after running scripts/gdrive_oauth_setup.py.
    # Not committed — this is a local secret, same category as an API key.
    gdrive_token_path: str = ".gdrive_token.json"


settings = Settings()