"""
Shared pytest configuration and fixtures.

sys.path is set once here so individual test files don't repeat it.
The `test_app` fixture creates a Flask app backed by an in-memory SQLite
database so tests run without any external service (no MySQL, no files).
"""
import os
import sys
from pathlib import Path

import pytest

# Make the backend package importable from any test file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def test_app():
    """
    Session-scoped Flask app using an in-memory SQLite database.

    All tables are created before the session and dropped after, giving
    each test session a clean, isolated schema.
    """
    os.environ.setdefault("LLM_PROVIDER", "mock")

    from app import create_app
    from models import db

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def app_ctx(test_app):
    """Push (and pop) an application context for tests that hit the DB directly."""
    with test_app.app_context():
        yield test_app


@pytest.fixture
def client(test_app):
    """Test client bound to the shared in-memory-DB app."""
    with test_app.test_client() as c:
        yield c
