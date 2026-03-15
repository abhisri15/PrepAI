"""
Data models for PrepAI.
Keeps persistence concerns minimal - SQLite/JSON compatible structures.
"""
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PROFILE_CONTEXT_FILE = DATA_DIR / "profile_context.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_profile_context_map() -> dict:
    ensure_data_dir()
    if not PROFILE_CONTEXT_FILE.exists():
        return {}
    with open(PROFILE_CONTEXT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_profile_context_map(data: dict):
    ensure_data_dir()
    with open(PROFILE_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def store_profile_context(user_id: str, payload: dict):
    """Store or update profile context used for personalized Q&A."""
    if not user_id:
        user_id = "anonymous"
    data = _load_profile_context_map()
    existing = data.get(user_id, {})
    merged = {**existing, **payload, "updated_at": datetime.utcnow().isoformat()}
    data[user_id] = merged
    _save_profile_context_map(data)
    return merged


def get_profile_context(user_id: str) -> dict:
    """Fetch profile context for a user, if available."""
    if not user_id:
        return {}
    data = _load_profile_context_map()
    return data.get(user_id, {})
