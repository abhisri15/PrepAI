"""
Shared utility helpers used across services.
Centralises logic that would otherwise be duplicated (e.g. JSON extraction).
"""
import json
import re


def parse_json_from_text(text: str) -> dict:
    """
    Extract the first valid JSON object from raw LLM output.

    Handles three common formats:
    1. Fenced code blocks: ```json { ... } ```
    2. Bare JSON object anywhere in the text
    3. Plain JSON string (no extra text)

    Falls back to wrapping the raw text under the 'answer' key so callers
    always receive a dict and never need to handle a parse failure themselves.
    """
    text = (text or "").strip()

    # 1. Strip markdown code fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    # 2. Find the first complete JSON object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Try the full text as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "improvements": [], "confidence": 0.5, "sources": []}
