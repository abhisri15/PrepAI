"""
LLM provider factory.

Resolves the configured provider name, caches one instance per provider
behind a threading.Lock (so concurrent Gunicorn threads don't race to
initialise the same client), and exposes convenience helpers for the
rest of the application.

Design pattern: Factory + Singleton (per-provider instance cache).
"""
import os
import threading

from config import Config
from services.llm.base import BaseLLMProvider
from services.llm.providers import (
    AnthropicProvider,
    GeminiProvider,
    GroqProvider,
    MockProvider,
    OpenAIProvider,
)
from utils.helpers import parse_json_from_text

# ── Provider registry ─────────────────────────────────────────────────────────

_REGISTRY: dict[str, type[BaseLLMProvider]] = {
    "mock":      MockProvider,
    "openai":    OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini":    GeminiProvider,
    "groq":      GroqProvider,
}

# ── Thread-safe instance cache ────────────────────────────────────────────────
# Providers are initialised at most once per resolved name. The lock prevents
# a race condition where two concurrent requests both try to build the same
# provider on first access.

_lock = threading.Lock()
_cache: dict[str, BaseLLMProvider] = {}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _resolve_auto() -> str:
    """Pick the best available provider based on which API keys are present."""
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.getenv("GOOGLE_API_KEY", "").strip():
        return "gemini"
    if Config.GROQ_API_KEY:
        return "groq"
    return "mock"


# ── Public factory functions ──────────────────────────────────────────────────

def get_provider(name: str = "auto") -> BaseLLMProvider:
    """
    Return a cached provider instance for *name*.

    Args:
        name: Provider key ("auto" | "mock" | "openai" | "anthropic" | "gemini" | "groq").
              "auto" selects the first provider whose API key is set in the environment.

    Returns:
        A thread-safe, reusable BaseLLMProvider instance.
    """
    resolved = _resolve_auto() if name in ("auto", "") else name.lower().strip()
    resolved = resolved if resolved in _REGISTRY else "mock"

    with _lock:
        if resolved not in _cache:
            _cache[resolved] = _REGISTRY[resolved]()
        return _cache[resolved]


def get_ask_provider() -> BaseLLMProvider:
    """
    Return the preferred provider for /api/ask.

    Uses Groq when GROQ_API_KEY is set (fast inference, < 1 s);
    falls back to the configured default provider otherwise.
    """
    if Config.GROQ_API_KEY:
        return get_provider("groq")
    return get_provider(Config.LLM_PROVIDER)


def generate_json(
    prompt: str,
    system: str = "",
    provider: BaseLLMProvider = None,
    **kwargs,
) -> dict:
    """
    Generate a response and parse it as JSON.

    Args:
        prompt:   User message.
        system:   Optional system message.
        provider: Override provider; uses default if omitted.
        **kwargs: Forwarded to provider.generate() (e.g. temperature, max_tokens).

    Returns:
        Parsed dict. Degrades gracefully if JSON parsing fails.
    """
    if provider is None:
        provider = get_provider()
    raw = provider.generate(prompt, system=system, **kwargs)
    return parse_json_from_text(raw)
