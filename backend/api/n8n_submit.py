"""
/api/n8n/submit - Proxy to n8n webhook for full prep guide flow.
Forwards resume + jd_url (or jd_text) to PrepAI Webhook Entry workflow.
"""
import os
import requests
from flask import Blueprint, request, jsonify

bp = Blueprint("n8n_submit", __name__)


@bp.route("/api/n8n/submit", methods=["POST"])
def submit():
    """
    Proxy to n8n PrepAI Webhook Entry.
    Request: { name, email, role, jd_url?, jd_text?, resume, additional_notes? }
    Requires N8N_PREPAI_WEBHOOK_URL in .env (e.g. http://localhost:5678/webhook/prepai-submit)
    """
    url = os.getenv("N8N_PREPAI_WEBHOOK_URL", "").strip()
    if not url:
        return jsonify({
            "error": "n8n webhook not configured. Set N8N_PREPAI_WEBHOOK_URL in .env",
            "example": "http://localhost:5678/webhook/prepai-submit"
        }), 503

    data = request.get_json() or {}
    payload = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "role": data.get("role", ""),
        "jd_url": data.get("jd_url", ""),
        "jd_text": data.get("jd_text", data.get("jd", "")),
        "resume": data.get("resume", data.get("resume_text", "")),
        "additional_notes": data.get("additional_notes", data.get("notes", "")),
    }

    if not payload.get("email") or not payload.get("resume"):
        return jsonify({"error": "email and resume are required"}), 400

    if not payload.get("jd_url") and not payload.get("jd_text"):
        return jsonify({"error": "Provide jd_url or jd_text"}), 400

    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException as e:
        return jsonify({"error": f"n8n request failed: {str(e)}"}), 502
