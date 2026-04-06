"""
n8n webhook client.
Handles sending payloads to n8n and normalising the varied response envelopes
that n8n nodes produce.
"""
import logging

import requests

from config import Config
from utils.helpers import parse_json_from_text

logger = logging.getLogger("prepai")


# ── Response normalisation ────────────────────────────────────────────────────

def unwrap_n8n_response(data) -> dict:
    """
    Recursively unwrap common n8n output envelopes.

    n8n nodes can wrap their output in several ways depending on node type:
    - Arrays:             [{ ... }]
    - json envelope:      { "json": { ... } }
    - body envelope:      { "body": { ... } }
    - data envelope:      { "data": { ... } }
    - message.content:    { "message": { "content": "<json string>" } }
    - output string:      { "output": "<json string>" }
    """
    if isinstance(data, list) and data:
        return unwrap_n8n_response(data[0])
    if not isinstance(data, dict):
        return data
    if isinstance(data.get("json"), dict):
        return unwrap_n8n_response(data["json"])
    if isinstance(data.get("body"), dict):
        return unwrap_n8n_response(data["body"])
    if isinstance(data.get("data"), dict):
        return unwrap_n8n_response(data["data"])

    # LangChain agent outputs text in message.content
    message = data.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        parsed = parse_json_from_text(message["content"])
        return parsed if parsed is not None else data

    output = data.get("output")
    if isinstance(output, str):
        parsed = parse_json_from_text(output)
        return parsed if parsed is not None else data

    return data


# ── Webhook calls ─────────────────────────────────────────────────────────────

def post_webhook(url: str, payload: dict, timeout: int = Config.N8N_TIMEOUT_SECS) -> dict:
    """
    POST *payload* to *url* and return the parsed, unwrapped response.

    Raises:
        requests.RequestException: On network / HTTP errors.
        ValueError: If the response body is empty or unparseable.
    """
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()

    text = response.text.strip()
    if not text:
        raise ValueError("Webhook returned an empty response body")

    try:
        return unwrap_n8n_response(response.json())
    except ValueError:
        parsed = parse_json_from_text(text)
        if parsed is None:
            raise ValueError("Webhook returned a response that could not be parsed as JSON")
        return unwrap_n8n_response(parsed)
