"""
Structured logging for PrepAI.
Centralises log formatting and provides request-scoped helpers.

Import this module instead of the standard `logging` to get consistent
formatting and request-ID tagging across all services.
"""
import logging
import sys

from flask import g

# Single shared logger for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("prepai")


def get_request_id() -> str:
    """Return the per-request ID set by the before_request middleware, or a fallback."""
    try:
        return getattr(g, "request_id", "no-rid")
    except RuntimeError:
        # Outside of request context (e.g. background threads, tests)
        return "no-rid"


def log_request(endpoint: str, model: str, latency_ms: float, **kwargs):
    """Log API request metadata with optional extra key=value pairs."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
    rid = get_request_id()
    logger.info("REQUEST | rid=%s | %s | model=%s | latency_ms=%.0f | %s", rid, endpoint, model, latency_ms, extra)


def log_prompt(prompt_preview: str, max_len: int = 200):
    """Log a truncated preview of the prompt sent to the LLM."""
    preview = prompt_preview[:max_len] + "..." if len(prompt_preview) > max_len else prompt_preview
    logger.info("PROMPT | rid=%s | %s", get_request_id(), preview)


def log_error(message: str, exc: Exception = None):
    """Log an error with optional exception details."""
    rid = get_request_id()
    if exc:
        logger.error("ERROR | rid=%s | %s | %s: %s", rid, message, type(exc).__name__, exc)
    else:
        logger.error("ERROR | rid=%s | %s", rid, message)
