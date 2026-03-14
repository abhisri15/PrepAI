"""
/api/prepare - Resume + JD → Preparation roadmap.
"""
import time
from flask import Blueprint, request, jsonify

from services.llm_provider import get_provider, generate_json
from services.prompt_templates import build_prep_prompt
from services.security import redact_pii
from utils.logging import log_request, log_prompt, logger

bp = Blueprint("prepare", __name__)


@bp.route("/api/prepare", methods=["POST"])
def prepare():
    """Generate preparation roadmap from resume and job description."""
    start = time.perf_counter()
    data = request.get_json() or {}
    resume_text = (data.get("resume_text") or "").strip()
    jd_text = (data.get("jd_text") or "").strip()

    if not resume_text or not jd_text:
        return jsonify({"error": "resume_text and jd_text are required"}), 400

    resume_text = redact_pii(resume_text)
    jd_text = redact_pii(jd_text)

    system, user_prompt = build_prep_prompt(resume_text, jd_text)
    full_prompt = f"{system}\n\n{user_prompt}"
    log_prompt(full_prompt[:300])

    try:
        result = generate_json(full_prompt, system=system, temperature=0.7, max_tokens=1024)
        def to_list(x):
            if isinstance(x, list):
                return x
            return [x] if x else []

        strengths = to_list(result.get("strengths", []))
        weaknesses = to_list(result.get("weaknesses", []))
        key_topics = to_list(result.get("key_topics", []))
        practice_questions = to_list(result.get("practice_questions", []))
        study_plan = to_list(result.get("study_plan", []))

        provider = get_provider()
        latency_ms = (time.perf_counter() - start) * 1000
        log_request("/api/prepare", provider.name, latency_ms)

        return jsonify({
            "strengths": list(strengths),
            "weaknesses": list(weaknesses),
            "key_topics": list(key_topics),
            "practice_questions": list(practice_questions),
            "study_plan": list(study_plan),
        })
    except Exception as e:
        logger.error(f"prepare error: {e}")
        return jsonify({
            "strengths": [],
            "weaknesses": [],
            "key_topics": [],
            "practice_questions": [],
            "study_plan": [],
        }), 500
