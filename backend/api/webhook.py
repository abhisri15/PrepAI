"""
Webhook callback endpoint.
n8n calls this after processing a submission so the backend can record
the qualification result and email-delivery status against the profile.
"""
import logging

from flask import Blueprint, jsonify, request

from repositories import profile_repo

logger = logging.getLogger("prepai")
bp = Blueprint("webhook", __name__)


@bp.route("/api/webhook/result", methods=["POST"])
def n8n_result():
    """
    Receive the outcome of an n8n workflow run.

    Expected JSON body:
        {
            "profile_id":  str,
            "qualified":   bool,
            "reason":      str   (optional — why the candidate was/wasn't qualified),
            "email_sent":  bool  (optional — whether the guide email was sent),
            "level":       str   (optional — "fresher" | "mid_level" | "senior")
        }

    Returns 200 even if profile_id is unknown so n8n does not retry endlessly.
    """
    data = request.get_json(silent=True) or {}
    profile_id = (data.get("profile_id") or "").strip()

    if not profile_id:
        logger.warning("n8n callback received with no profile_id")
        return jsonify({"status": "ignored", "reason": "no profile_id"}), 200

    if not profile_repo.get(profile_id):
        logger.warning("n8n callback for unknown profile_id=%s", profile_id)
        return jsonify({"status": "ignored", "reason": "profile not found"}), 200

    update = {}
    if "qualified" in data:
        update["n8n_qualified"] = bool(data["qualified"])
    if "reason" in data:
        update["n8n_reason"] = str(data["reason"])
    if "email_sent" in data:
        update["n8n_email_sent"] = bool(data["email_sent"])
    if "level" in data:
        update["n8n_level"] = str(data["level"])

    if update:
        profile_repo.save(profile_id, update)
        logger.info("n8n callback applied | profile_id=%s | fields=%s", profile_id, list(update.keys()))

    return jsonify({"status": "ok"}), 200
