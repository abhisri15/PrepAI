"""
PrepAI Flask Backend.
Clean architecture: API routes delegate to services.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from api.ask import bp as ask_bp
from api.profile import bp as profile_bp
from services.llm_provider import get_provider

# Load env from project root or backend dir
root = Path(__file__).parent.parent
for p in (root / ".env", Path(__file__).parent / ".env"):
    if p.exists():
        load_dotenv(p)
        break

app = Flask(__name__)
CORS(app, origins=["*"])

app.register_blueprint(ask_bp)
app.register_blueprint(profile_bp)


@app.route("/")
def index():
    """Basic root endpoint so platform HTTP probes get a fast 200 response."""
    return {"service": "PrepAI", "status": "ok"}


@app.route("/health")
def health():
    """Health check for frontend and monitoring."""
    provider = get_provider()
    return {
        "status": "ok",
        "model": os.getenv("LLM_MODEL", "mock"),
        "provider": provider.name,
        "version": "1.0",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "true").lower() == "true")
