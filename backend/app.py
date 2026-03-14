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
from api.evaluate import bp as evaluate_bp
from api.prepare import bp as prepare_bp
from api.upload import bp as upload_bp
from api.feedback import bp as feedback_bp
from api.webhook import bp as webhook_bp
from services.llm_provider import get_provider

# Load env from project root or backend dir
root = Path(__file__).parent.parent
for p in (root / ".env", Path(__file__).parent / ".env"):
    if p.exists():
        load_dotenv(p)
        break

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

app.register_blueprint(ask_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(prepare_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(webhook_bp)


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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "true").lower() == "true")
