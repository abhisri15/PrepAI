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
