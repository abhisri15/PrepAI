"""
PII redaction before sending user data to AI providers.

Scrubs the most common personally identifiable information (email addresses,
phone numbers, credit-card numbers) from text to limit exposure to third-party
LLM APIs. Applied to every user-supplied prompt in /api/ask.
"""
import re

# ── Compiled regex patterns ───────────────────────────────────────────────────

# Standard email addresses: user@domain.tld
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Phone numbers: international (+91), US (555-123-4567), and common separators
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

# Credit / debit card numbers: groups of 4 digits separated by space, dash, or dot
_CARD_RE = re.compile(r"\b(?:\d{4}[-.\s]?){3}\d{4}\b")


# ── Public API ────────────────────────────────────────────────────────────────

def redact_pii(text: str) -> str:
    """
    Redact PII from *text* before sending it to an AI provider.

    Handles:
    - Email addresses  → [EMAIL_REDACTED]
    - Phone numbers    → [PHONE_REDACTED]
    - Credit-card nums → [CARD_REDACTED]

    Returns the original value unchanged if it is not a non-empty string.
    """
    if not text or not isinstance(text, str):
        return text
    text = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = _PHONE_RE.sub("[PHONE_REDACTED]", text)
    text = _CARD_RE.sub("[CARD_REDACTED]", text)
    return text
