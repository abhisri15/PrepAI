"""Tests for profile orchestration endpoint."""
import os
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
import models
import services.retriever as retriever


def test_prep_guide_stores_profile_and_calls_webhook(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())

    models.DATA_DIR = temp_dir
    models.FEEDBACK_FILE = temp_dir / "feedback.json"
    models.PROFILE_CONTEXT_FILE = temp_dir / "profile_context.json"
    models.UPLOADS_DIR = temp_dir / "uploads"

    retriever.DATA_DIR = temp_dir
    retriever.CHUNKS_FILE = temp_dir / "chunks.json"
    retriever.EMBEDDINGS_DIR = temp_dir / "embeddings"

    os.environ["N8N_FORM_WEBHOOK_URL"] = "https://example.test/webhook/prepai-form-submit"
    os.environ["LLM_PROVIDER"] = "mock"

    captured = {}

    def fake_post_webhook(url, payload, timeout=45):
        captured["url"] = url
        captured["payload"] = payload
        return {"message": "Detailed prep guide will be sent via email."}

    def fake_summarize_profile_async(profile_id, **kwargs):
        models.store_profile_context(profile_id, {
            "summary_status": "complete",
            "summary": "Candidate matches backend Python/API roles.",
            "summary_context": "Candidate matches backend Python/API roles.",
        })

    from api import profile as profile_api

    monkeypatch.setattr(profile_api, "post_webhook", fake_post_webhook)
    monkeypatch.setattr(profile_api, "summarize_profile_async", fake_summarize_profile_async)

    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/api/prep-guide", json={
            "name": "Test User",
            "email": "test@example.com",
            "role": "Backend Engineer",
            "resume_text": "Python Flask APIs",
            "jd_text": "Build backend services and APIs",
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Detailed prep guide will be sent via email."
    assert captured["url"] == "https://example.test/webhook/prepai-form-submit"
    assert captured["payload"]["jd_text"] == "Build backend services and APIs"
    stored = models.get_profile_context(data["profile_id"])
    assert stored["summary_status"] == "complete"