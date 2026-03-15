"""Tests for prompt templates."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.prompt_templates import build_ask_prompt


def test_build_ask_prompt():
    system, user = build_ask_prompt("What is REST?", "some context")
    assert "REST" in user
    assert "some context" in user
    assert "interview" in system.lower()
