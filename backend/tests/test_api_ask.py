"""Tests for /api/ask endpoint."""
import os
import pytest
from app import app


@pytest.fixture
def client():
    os.environ["LLM_PROVIDER"] = "mock"
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_ask_requires_question(client):
    r = client.post("/api/ask", json={})
    assert r.status_code == 400
    assert b"question" in r.data.lower()


def test_ask_returns_json(client):
    r = client.post("/api/ask", json={"question": "What is REST?"})
    assert r.status_code == 200
    data = r.get_json()
    assert "answer" in data
    assert "improvements" in data
    assert "confidence" in data
    assert "sources" in data
    assert isinstance(data["answer"], str)
    assert 0 <= data["confidence"] <= 1
