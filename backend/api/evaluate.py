"""
/api/evaluate - Evaluate candidate answer.
"""
import time
from flask import Blueprint, request, jsonify

from services.llm_provider import generate_json
from services.prompt_templates import build_evaluate_prompt
from services.security import redact_pii
from utils.logging import log_request, log_prompt, logger
from services.llm_provider import get_provider

bp = Blueprint("evaluate", __name__)


@bp.route("/api/evaluate", methods=["POST"])
def evaluate():
    """Score candidate answer and suggest improvements."""
    start = time.perf_counter()
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    candidate_answer = (data.get("candidate_answer") or "").strip()

    if not question or not candidate_answer:
        return jsonify({"error": "question and candidate_answer are required"}), 400

    question = redact_pii(question)
    candidate_answer = redact_pii(candidate_answer)

    system, user_prompt = build_evaluate_prompt(question, candidate_answer)
    full_prompt = f"{system}\n\n{user_prompt}"
    log_prompt(full_prompt[:300])

    try:
        result = generate_json(full_prompt, system=system, temperature=0.5, max_tokens=512)
        score = float(result.get("score", 0))
        rationale = result.get("rationale", "")
        improvements = result.get("improvements", [])
        if isinstance(improvements, str):
            improvements = [improvements] if improvements else []
        confidence = float(result.get("confidence", 0.5))

        provider = get_provider()
        latency_ms = (time.perf_counter() - start) * 1000
        log_request("/api/evaluate", provider.name, latency_ms)

        return jsonify({
            "score": score,
            "rationale": rationale,
            "improvements": improvements,
            "confidence": confidence,
        })
    except Exception as e:
        logger.error(f"evaluate error: {e}")
        return jsonify({
            "score": 0,
            "rationale": "Evaluation failed.",
            "improvements": [],
            "confidence": 0,
        }), 500
