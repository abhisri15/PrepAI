"""
PII redaction before sending prompts to AI providers.
Removes emails, phone numbers, credit cards.
"""
import re


# Patterns for PII detection
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
)
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[-.\s]?){3}\d{4}\b"
)


def redact_emails(text: str) -> str:
    return EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)


def redact_phones(text: str) -> str:
    return PHONE_PATTERN.sub("[PHONE_REDACTED]", text)


def redact_credit_cards(text: str) -> str:
    return CREDIT_CARD_PATTERN.sub("[CARD_REDACTED]", text)


def redact_pii(text: str) -> str:
    """
    Redact PII from text before sending to AI.
    Handles emails, phone numbers, credit card numbers.
    """
    if not text or not isinstance(text, str):
        return text
    result = redact_emails(text)
    result = redact_phones(result)
    result = redact_credit_cards(result)
    return result
