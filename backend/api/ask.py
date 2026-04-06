"""
/api/ask — AI interview Q&A with full profile context.

Groq is used when GROQ_API_KEY is set (fast inference); falls back to the
configured default provider otherwise.
"""
import logging
import time

from flask import Blueprint, jsonify, request

from config import Config
from repositories import conversation_repo, profile_repo
from services.llm import generate_json, get_ask_provider
from services.pii_guard import redact_pii
from services.prompt_builder import build_ask_prompt
from utils.logger import log_prompt, log_request

logger = logging.getLogger("prepai")
bp = Blueprint("ask", __name__)


def _build_full_context(profile: dict) -> str:
    """
    Assemble the LLM context block from a stored profile.

    Uses the AI-generated summary when available (richer, more compact).
    Falls back to raw resume + JD text with conservative char limits.
    """
    summary = (profile.get("summary_context") or profile.get("summary") or "").strip()
    if summary:
        return f"Candidate profile summary:\n{summary}"

    parts = []
    resume = (profile.get("resume_text") or "").strip()
    jd = (profile.get("jd_text") or "").strip()
    if resume:
        parts.append(f"Resume:\n{resume[:Config.RESUME_MAX_CHARS]}")
    if jd:
        parts.append(f"Job description:\n{jd[:Config.JD_MAX_CHARS]}")
    return "\n\n".join(parts)


@bp.route("/api/ask", methods=["POST"])
def ask():
    """
    Answer an interview question personalised to the candidate's profile.

    Request JSON:
        {
            "question": str,        # required
            "user_id":  str,        # optional — profile_id to load context from
            "context":  str         # optional — overrides profile context
        }

    Response JSON:
        {
            "answer":       str,
            "improvements": list[str],
            "confidence":   float,
            "sources":      list[str]
        }
    """
    start = time.perf_counter()
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    context_override = (body.get("context") or "").strip()
    user_id = (body.get("user_id") or "anonymous").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    # Redact PII before the question reaches the LLM
    question = redact_pii(question)
    provider = get_ask_provider()

    # Build context: explicit override → stored profile → empty fallback
    if context_override:
        full_context = context_override
    else:
        profile = profile_repo.get(user_id)
        full_context = _build_full_context(profile)

    if not full_context:
        full_context = "(No profile selected — submit a Prep Guide first, then select a profile in Ask.)"

    system_msg, user_msg = build_ask_prompt(question, full_context)
    log_prompt(f"{system_msg[:80]}... {user_msg[:150]}")

    try:
        result = generate_json(
            user_msg,
            system=system_msg,
            provider=provider,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS,
        )

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

        if user_id and user_id != "anonymous" and profile_repo.exists(user_id):
            try:
                conversation_repo.add(
                    profile_id=user_id,
                    question=question,
                    answer=answer,
                    confidence=confidence,
                    improvements=improvements,
                    sources=sources,
                )
            except Exception as save_err:  # noqa: BLE001
                logger.warning("Failed to save conversation: %s", save_err)

        return jsonify({
            "answer": answer,
            "improvements": improvements,
            "confidence": confidence,
            "sources": sources,
        })

    except (ValueError, KeyError, RuntimeError) as exc:
        logger.error("ask handler error (expected): %s: %s", type(exc).__name__, exc)
        return jsonify({
            "answer": "Sorry, something went wrong processing your question. Please try again.",
            "improvements": [],
            "confidence": 0.0,
            "sources": [],
        }), 500
    except Exception as exc:  # noqa: BLE001 — catch-all so the endpoint never 500 silently
        logger.exception("ask handler unexpected error: %s", exc)
        return jsonify({
            "answer": "An unexpected error occurred. Please try again.",
            "improvements": [],
            "confidence": 0.0,
            "sources": [],
        }), 500


@bp.route("/api/conversations/<profile_id>", methods=["GET"])
def get_conversations(profile_id: str):
    """Return recent Q&A history for a profile (newest first)."""
    limit = request.args.get("limit", 50, type=int)
    conversations = conversation_repo.list_by_profile(profile_id, limit=min(limit, 200))
    return jsonify({"conversations": conversations, "count": len(conversations)})
