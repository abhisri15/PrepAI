"""/api/fetch-jd - Fetch job description text from a URL."""
from flask import Blueprint, request, jsonify

from services.jd_fetcher import fetch_job_description

bp = Blueprint("fetch_jd", __name__)


@bp.route("/api/fetch-jd", methods=["POST"])
def fetch_jd():
    """
    Fetch job description from URL.
    Request: { "jd_url": "https://..." }
    Response: { "jd_text": "...", "url": "..." }
    """
    data = request.get_json() or {}
    jd_url = (data.get("jd_url") or data.get("url") or "").strip()
    if not jd_url:
        return jsonify({"error": "jd_url is required"}), 400

    try:
        text = fetch_job_description(jd_url)
        return jsonify({"jd_text": text, "url": jd_url})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Could not fetch URL: {str(e)}"}), 400
