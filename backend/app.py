"""
PrepAI Flask application factory.
Call create_app() to get a configured Flask instance.
Tests and wsgi.py both use this function to avoid a shared global app object.
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, request
from flask_cors import CORS

from flask_migrate import Migrate

from config import Config
from models import db
from utils.logger import logger


def _load_env():
    """Load .env from project root or backend directory (first match wins)."""
    root = Path(__file__).parent.parent
    for candidate in (root / ".env", Path(__file__).parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            break


def _validate_startup_config(cfg: Config):
    """Warn about missing optional keys; log clearly if critical ones are absent."""
    if not cfg.N8N_WEBHOOK_URL:
        logger.info(
            "N8N_PREPAI_WEBHOOK_URL is not set — n8n email mode unavailable. "
            "Instant Guide mode works without it."
        )
    if not cfg.GROQ_API_KEY:
        logger.info("GROQ_API_KEY not set — /api/ask will use the fallback LLM provider.")


def create_app(config: Config = None) -> Flask:
    """
    Application factory.

    Args:
        config: Optional Config instance (useful for tests to pass overrides).

    Returns:
        Configured Flask application.
    """
    _load_env()

    app = Flask(__name__)
    cfg = config or Config()
    app.config.from_object(cfg)

    _validate_startup_config(cfg)

    # ── Database ──────────────────────────────────────────────────────────────
    app.config["SQLALCHEMY_DATABASE_URI"] = cfg.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.create_all()  # idempotent; in prod run `flask db upgrade` instead

    # CORS — origins controlled via CORS_ORIGINS env var
    CORS(app, origins=cfg.CORS_ORIGINS)

    # Attach a short request ID to every request for log correlation
    @app.before_request
    def _assign_request_id():
        g.request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])

    _register_blueprints(app)
    _register_health_routes(app, cfg)

    return app


def _register_blueprints(app: Flask):
    from api.ask import bp as ask_bp
    from api.ats import bp as ats_bp
    from api.profile import bp as profile_bp
    from api.webhook import bp as webhook_bp

    app.register_blueprint(ask_bp)
    app.register_blueprint(ats_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(webhook_bp)


def _register_health_routes(app: Flask, cfg: Config):
    from services.llm import get_provider

    @app.route("/")
    def index():
        """Root probe — fast 200 for platform health checks."""
        return {"service": "PrepAI", "status": "ok"}

    @app.route("/health")
    def health():
        """Detailed health check used by the frontend Header component."""
        provider = get_provider()
        return {
            "status": "ok",
            "model": cfg.LLM_MODEL,
            "provider": provider.name,
            "version": "1.0",
        }
