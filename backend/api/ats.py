"""
/api/ats-score — Resume vs JD ATS compatibility analysis.
"""
import logging

from flask import Blueprint, jsonify, request

from repositories import profile_repo
from services.ats_scorer import compute_ats_score

logger = logging.getLogger("prepai")
bp = Blueprint("ats", __name__)


@bp.route("/api/ats-score", methods=["POST"])
def ats_score():
    """
    Compute ATS compatibility score for a profile's resume vs JD.

    Request JSON:
        { "profile_id": str }            — use stored resume + JD
        OR
        { "resume_text": str, "jd_text": str }  — ad-hoc analysis

    Response JSON:
        {
            "score": int,
            "matched_keywords": [...],
            "missing_keywords": [...],
            "category_scores": { "skills": int, "experience": int, "education": int, "keywords": int },
            "suggestions": [...],
            "summary": str
        }
    """
    body = request.get_json(silent=True) or {}
    profile_id = (body.get("profile_id") or "").strip()
    resume_text = (body.get("resume_text") or "").strip()
    jd_text = (body.get("jd_text") or "").strip()

    if profile_id and (not resume_text or not jd_text):
        profile = profile_repo.get(profile_id)
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        resume_text = resume_text or (profile.get("resume_text") or "").strip()
        jd_text = jd_text or (profile.get("jd_text") or "").strip()

    if not resume_text:
        return jsonify({"error": "resume_text is required (or provide a valid profile_id)"}), 400
    if not jd_text:
        return jsonify({"error": "jd_text is required (or provide a valid profile_id)"}), 400

    try:
        result = compute_ats_score(resume_text, jd_text)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ATS score computation failed: %s", exc)
        return jsonify({"error": "Failed to compute ATS score. Please try again."}), 500
