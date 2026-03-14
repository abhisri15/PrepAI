"""
/api/fetch-jd - Fetch job description text from a URL.
Used by n8n workflows when user provides JD link instead of raw text.
"""
import re
from flask import Blueprint, request, jsonify
import requests
from urllib.parse import urlparse

bp = Blueprint("fetch_jd", __name__)


def _extract_text(html: str) -> str:
    """Simple HTML-to-text extraction without BeautifulSoup."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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

    parsed = urlparse(jd_url)
    if not parsed.scheme or not parsed.netloc:
        return jsonify({"error": "Invalid URL"}), 400

    try:
        r = requests.get(jd_url, timeout=15, headers={"User-Agent": "PrepAI/1.0"})
        r.raise_for_status()
        text = _extract_text(r.text)
        return jsonify({"jd_text": text[:15000], "url": jd_url})
    except requests.RequestException as e:
        return jsonify({"error": f"Could not fetch URL: {str(e)}"}), 400
