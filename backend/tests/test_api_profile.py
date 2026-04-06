"""Tests for profile orchestration endpoints (/api/prep-guide, /api/profile/<id>)."""
import os

import pytest

import services.retriever as retriever


def test_prep_guide_stores_profile_and_calls_webhook(test_app, monkeypatch):
    """
    End-to-end test: POST /api/prep-guide stores profile in DB, fires webhook,
    and kicks off the (mocked) async summarisation.
    """
    os.environ["N8N_PREPAI_WEBHOOK_URL"] = "https://example.test/webhook/interview-prep"

    captured: dict = {}

    def fake_post_webhook(url, payload, timeout=None):
        captured["url"] = url
        captured["payload"] = payload
        return {"message": "Detailed prep guide will be sent via email."}

    def fake_summarize_async(profile_id, **kwargs):
        # Run synchronously inside the test's app context so the DB write succeeds.
        from repositories import profile_repo
        profile_repo.save(profile_id, {
            "summary_status": "complete",
            "summary": "Candidate matches backend Python/API roles.",
            "summary_context": "Candidate matches backend Python/API roles.",
        })

    from api import profile as profile_api
    monkeypatch.setattr(profile_api, "post_webhook", fake_post_webhook)
    monkeypatch.setattr(profile_api, "summarize_profile_async", fake_summarize_async)

    with test_app.app_context():
        with test_app.test_client() as client:
            response = client.post("/api/prep-guide", json={
                "mode": "n8n",
                "name": "Test User",
                "email": "test@example.com",
                "role": "Backend Engineer",
                "resume_text": "Python Flask APIs",
                "jd_text": "Build backend services and APIs",
            })

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Detailed prep guide will be sent via email."
        assert captured["url"] == "https://example.test/webhook/interview-prep"
        assert captured["payload"].get("Resume text") == "Python Flask APIs"
        assert captured["payload"].get("Or paste job description text") == "Build backend services and APIs"

        from repositories import profile_repo
        stored = profile_repo.get(data["profile_id"])
        assert stored["summary_status"] == "complete"
