"""
/api/webhook - n8n workflow endpoint.
IMPORTANT: Preserve existing workflow payload format.
Adapt backend to support the workflow, do NOT change the n8n flow.
"""
import time
from flask import Blueprint, request, jsonify

from services.llm_provider import get_provider, generate_json
from services.prompt_templates import build_ask_prompt, build_evaluate_prompt, build_prep_prompt
from services.retriever import get_context_for_query
from services.security import redact_pii
from utils.logging import log_request, logger

bp = Blueprint("webhook", __name__)


def _handle_webhook_ask(data: dict) -> dict:
    """Handle ask-type webhook payload."""
    question = (data.get("question") or data.get("query") or "").strip()
    if not question:
        return {"error": "question or query required"}
    question = redact_pii(question)
    context = get_context_for_query(question, top_k=3)
    system, user_prompt = build_ask_prompt(question, context)
    result = generate_json(user_prompt, system=system)
    return {
        "answer": result.get("answer", ""),
        "improvements": result.get("improvements", []),
        "confidence": result.get("confidence", 0.5),
        "sources": result.get("sources", []),
    }


def _handle_webhook_evaluate(data: dict) -> dict:
    """Handle evaluate-type webhook payload."""
    question = (data.get("question") or "").strip()
    candidate_answer = (data.get("candidate_answer") or data.get("answer") or "").strip()
    if not question or not candidate_answer:
        return {"error": "question and candidate_answer required"}
    question = redact_pii(question)
    candidate_answer = redact_pii(candidate_answer)
    system, user_prompt = build_evaluate_prompt(question, candidate_answer)
    result = generate_json(user_prompt, system=system)
    return {
        "score": result.get("score", 0),
        "rationale": result.get("rationale", ""),
        "improvements": result.get("improvements", []),
        "confidence": result.get("confidence", 0.5),
    }


def _handle_webhook_prepare(data: dict) -> dict:
    """Handle prepare-type webhook payload."""
    resume_text = (data.get("resume_text") or data.get("resume") or "").strip()
    jd_text = (data.get("jd_text") or data.get("job_description") or data.get("jd") or "").strip()
    if not resume_text or not jd_text:
        return {"error": "resume_text and jd_text required"}
    resume_text = redact_pii(resume_text)
    jd_text = redact_pii(jd_text)
    system, user_prompt = build_prep_prompt(resume_text, jd_text)
    result = generate_json(user_prompt, system=system)
    return {
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "key_topics": result.get("key_topics", []),
        "practice_questions": result.get("practice_questions", []),
        "study_plan": result.get("study_plan", []),
    }


@bp.route("/api/webhook", methods=["POST"])
def webhook():
    """
    n8n webhook endpoint. Accepts existing workflow payload format.
    Supports: action=ask | evaluate | prepare
    """
    start = time.perf_counter()
    data = request.get_json() or {}
    action = (data.get("action") or data.get("type") or "ask").lower()

    provider = get_provider()
    handler = {
        "ask": _handle_webhook_ask,
        "evaluate": _handle_webhook_evaluate,
        "prepare": _handle_webhook_prepare,
    }.get(action, _handle_webhook_ask)

    try:
        result = handler(data)
        latency_ms = (time.perf_counter() - start) * 1000
        log_request("/api/webhook", provider.name, latency_ms, action=action)
        return jsonify(result)
    except Exception as e:
        logger.error(f"webhook error: {e}")
        return jsonify({"error": str(e)}), 500
