"""Helpers for invoking n8n workflows and normalizing their responses."""
import json
import re
import threading

import requests


def _extract_json_from_text(text: str):
    text = (text or "").strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.I)
    candidate = fenced.group(1).strip() if fenced else text
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def unwrap_n8n_response(data):
    """Handle common n8n node output envelopes."""
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
    message = data.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        parsed = _extract_json_from_text(message["content"])
        return parsed if parsed is not None else data
    output = data.get("output")
    if isinstance(output, str):
        parsed = _extract_json_from_text(output)
        return parsed if parsed is not None else data
    return data


def post_webhook(url: str, payload: dict, timeout: int = 45):
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        raise ValueError("Webhook returned an empty response")
    try:
        return unwrap_n8n_response(response.json())
    except ValueError:
        parsed = _extract_json_from_text(text)
        if parsed is None:
            raise ValueError("Webhook returned invalid JSON")
        return unwrap_n8n_response(parsed)


def trigger_webhook_async(url: str, payload: dict, timeout: int = 20):
    def _runner():
        try:
            requests.post(url, json=payload, timeout=timeout)
        except requests.RequestException:
            return

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return thread