"""Tests for prompt_builder service."""
from services.prompt_builder import build_ask_prompt


def test_build_ask_prompt_returns_tuple():
    system, user = build_ask_prompt("Tell me about yourself", "Resume: Senior engineer at Acme")
    assert isinstance(system, str) and len(system) > 0
    assert isinstance(user, str) and len(user) > 0


def test_build_ask_prompt_injects_context():
    context = "Resume: 5 years Python experience"
    _, user = build_ask_prompt("What are your strengths?", context)
    assert context in user


def test_build_ask_prompt_empty_context_fallback():
    _, user = build_ask_prompt("What is REST?", "")
    assert "No profile context" in user
