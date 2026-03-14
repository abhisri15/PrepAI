"""
/api/feedback - Store feedback locally.
"""
from flask import Blueprint, request, jsonify

from models import store_feedback

bp = Blueprint("feedback", __name__)


@bp.route("/api/feedback", methods=["POST"])
def feedback():
    """Store user feedback for analysis."""
    data = request.get_json() or {}
    user_id = data.get("user_id") or "anonymous"
    endpoint = data.get("endpoint", "")
    payload = data.get("payload", {})
    response = data.get("response", {})

    try:
        store_feedback(user_id, endpoint, payload, response)
        return jsonify({"status": "ok", "message": "Feedback stored"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
