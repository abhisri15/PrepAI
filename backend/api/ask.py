"""
/api/ask - AI interview Q&A with optional RAG context.
"""
import time
from flask import Blueprint, request, jsonify

from services.llm_provider import get_provider, generate_json
from services.prompt_templates import build_ask_prompt
from services.retriever import get_context_for_query
from services.security import redact_pii
from utils.logging import log_request, log_prompt, logger

bp = Blueprint("ask", __name__)


@bp.route("/api/ask", methods=["POST"])
def ask():
    """Handle interview Q&A. Uses RAG context if available."""
    start = time.perf_counter()
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    context_override = data.get("context", "").strip()
    user_id = data.get("user_id") or "anonymous"

    if not question:
        return jsonify({"error": "question is required"}), 400

    question = redact_pii(question)
    provider = get_provider()

    # Use provided context or retrieve from vector store
    retrieved_context = context_override or get_context_for_query(question, top_k=3)

    system, user_prompt = build_ask_prompt(question, retrieved_context)
    log_prompt(f"{system[:100]}... {user_prompt[:200]}")

    try:
        result = generate_json(user_prompt, system=system, temperature=0.7, max_tokens=1024)
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
