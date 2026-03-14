"""Tests for prompt templates."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.prompt_templates import (
    build_ask_prompt,
    build_evaluate_prompt,
    build_prep_prompt,
)


def test_build_ask_prompt():
    system, user = build_ask_prompt("What is REST?", "some context")
    assert "REST" in user
    assert "some context" in user
    assert "interview" in system.lower()


def test_build_evaluate_prompt():
    system, user = build_evaluate_prompt("What is REST?", "REST is an API style.")
    assert "REST" in user
    assert "REST is an API style" in user


def test_build_prep_prompt():
    system, user = build_prep_prompt("Resume text", "JD text")
    assert "Resume text" in user
    assert "JD text" in user
