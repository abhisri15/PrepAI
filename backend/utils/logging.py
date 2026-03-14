"""
Structured logging for PrepAI.
Logs requests, prompts, model used, and latency.
"""
import logging
import sys
import time
from functools import wraps

# Configure structured logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("prepai")


def log_request(endpoint: str, model: str, latency_ms: float, **kwargs):
    """Log API request metadata."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
    logger.info(f"REQUEST | {endpoint} | model={model} | latency_ms={latency_ms:.0f} | {extra}")


def log_prompt(prompt_preview: str, max_len: int = 200):
    """Log prompt sent to LLM (truncated for privacy)."""
    preview = prompt_preview[:max_len] + "..." if len(prompt_preview) > max_len else prompt_preview
    logger.info(f"PROMPT | {preview}")


def log_error(message: str, exc: Exception = None):
    """Log error with optional exception."""
    if exc:
        logger.error(f"ERROR | {message} | {type(exc).__name__}: {exc}")
    else:
        logger.error(f"ERROR | {message}")


def with_timing(f):
    """Decorator to measure and log function execution time."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = f(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f"LATENCY | {f.__name__} | {elapsed_ms:.0f}ms")
        return result

    return wrapper
