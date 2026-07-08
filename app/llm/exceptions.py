class LLMError(Exception):
    """Base class for all LLM-provider errors raised by this app."""


class LLMRateLimitError(LLMError):
    """Raised when a provider signals we've hit a rate/quota limit.

    The client catches this specifically to trigger fallback — other errors
    (auth failures, bad requests) are not retried onto a fallback provider,
    since retrying a malformed request elsewhere just wastes another call.
    """


class LLMConfigError(LLMError):
    """Raised when a provider is selected but missing required config (e.g. no API key)."""
