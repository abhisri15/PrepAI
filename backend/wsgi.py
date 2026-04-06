"""
WSGI entry point for Gunicorn / Render.

IMPORTANT: dotenv must be loaded BEFORE any app imports so that
os.getenv() calls inside Config class attributes (evaluated at import
time) pick up values from .env. Importing app.py first would evaluate
Config with default/empty values, ignoring the .env file entirely.

Production:  gunicorn wsgi:app --bind 0.0.0.0:$PORT
Local dev:   python wsgi.py
"""
# ── 1. Load .env FIRST — before any local import ─────────────────────────────
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)

# ── 2. Now it is safe to import Config and create the app ─────────────────────
from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # use_reloader=False avoids watchdog restarts (e.g. touching site-packages) that
    # drop in-flight browser requests and show "Failed to fetch" on the frontend.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=app.config.get("DEBUG", False),
        use_reloader=False,
    )
