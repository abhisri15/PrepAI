"""
/api/ask - AI interview Q&A with full profile context. Uses Groq when GROQ_API_KEY is set.
"""
import time
from flask import Blueprint, request, jsonify

from services.llm_provider import get_ask_provider, generate_json
from services.prompt_templates import build_ask_prompt
from services.security import redact_pii
from utils.logging import log_request, log_prompt, logger
from models import get_profile_context

bp = Blueprint("ask", __name__)


def _full_profile_context(profile: dict) -> str:
    """Build full context from profile: summary if available, else resume + JD (truncated)."""
    summary = (profile.get("summary_context") or profile.get("summary") or "").strip()
    if summary:
        return f"Candidate profile summary:\n{summary}"
    parts = []
    resume_text = (profile.get("resume_text") or "").strip()
    jd_text = (profile.get("jd_text") or "").strip()
    if resume_text:
        parts.append(f"Resume:\n{resume_text[:6000]}")
    if jd_text:
        parts.append(f"Job description:\n{jd_text[:4000]}")
    if not parts:
        return ""
    return "\n\n".join(parts)


@bp.route("/api/ask", methods=["POST"])
def ask():
    """Handle interview Q&A. Sends full profile context (resume + JD or summary) to LLM for personalized answers."""
    start = time.perf_counter()
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    context_override = data.get("context", "").strip()
    user_id = data.get("user_id") or "anonymous"

    if not question:
        return jsonify({"error": "question is required"}), 400

    question = redact_pii(question)
    provider = get_ask_provider()

    # Full context from selected profile for personalized answers
    profile = get_profile_context(user_id)
    if context_override:
        full_context = context_override
    else:
        full_context = _full_profile_context(profile)
    if not full_context:
        full_context = "(No profile selected. Submit Prep Guide first and select a profile in Ask.)"

    system, user_prompt = build_ask_prompt(question, full_context)
    log_prompt(f"{system[:100]}... {user_prompt[:200]}")

    try:
        result = generate_json(user_prompt, system=system, provider=provider, temperature=0.7, max_tokens=1024)
        # Normalize keys for response
        answer = result.get("answer", "")
        improvements = result.get("improvements", [])
        if isinstance(improvements, str):
            improvements = [improvements] if improvements else []
        confidence = float(result.get("confidence", 0.5))
        sources = result.get("sources", [])
        if isinstance(sources, str):
            sources = [sources] if sources else []

        latency_ms = (time.perf_counter() - start) * 1000
        log_request("/api/ask", provider.name, latency_ms, user_id=user_id)

        return jsonify({
            "answer": answer,
            "improvements": improvements,
            "confidence": confidence,
            "sources": sources,
        })
    except Exception as e:
        logger.error(f"ask error: {e}")
        return jsonify({
            "answer": "Sorry, I encountered an error. Please try again.",
            "improvements": [],
            "confidence": 0,
            "sources": [],
        }), 500
