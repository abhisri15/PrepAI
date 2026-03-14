"""
Data models for PrepAI.
Keeps persistence concerns minimal - SQLite/JSON compatible structures.
"""
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.json"
PROFILE_CONTEXT_FILE = DATA_DIR / "profile_context.json"
UPLOADS_DIR = DATA_DIR / "uploads"


def ensure_data_dir():
    """Create data directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "embeddings").mkdir(parents=True, exist_ok=True)


def store_feedback(user_id: str, endpoint: str, payload: dict, response: dict):
    """Store feedback locally (append to JSON file)."""
    ensure_data_dir()
    entry = {
        "user_id": user_id,
        "endpoint": endpoint,
        "payload": payload,
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
    }
    entries = []
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r") as f:
            entries = json.load(f)
    entries.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def get_feedback_entries(limit: int = 50):
    """Retrieve recent feedback entries."""
    ensure_data_dir()
    if not FEEDBACK_FILE.exists():
        return []
    with open(FEEDBACK_FILE, "r") as f:
        entries = json.load(f)
    return entries[-limit:]


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
