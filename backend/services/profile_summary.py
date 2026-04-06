"""
Asynchronous profile summarisation using the configured LLM provider.

The summary runs in a background daemon thread so the /api/prep-guide
response is returned immediately. Phase 4 will migrate this to a Celery task.
"""
import json
import logging
import threading

from flask import current_app

from config import Config
from models.db import db
from repositories import profile_repo
from services.llm import generate_json

logger = logging.getLogger("prepai")

_SUMMARY_SYSTEM = (
    "You are an interview preparation analyst. Summarise a candidate's profile and "
    "target role for personalised interview coaching. Return only valid JSON."
)


def _build_summary_prompt(name: str, role: str, resume_text: str, jd_text: str, additional_notes: str) -> str:
    return (
        f"Candidate name: {name}\n"
        f"Target role: {role}\n\n"
        f"Resume:\n{resume_text[:Config.SUMMARY_RESUME_MAX_CHARS]}\n\n"
        f"Job description:\n{jd_text[:Config.SUMMARY_JD_MAX_CHARS]}\n\n"
        f"Additional notes:\n{additional_notes}\n\n"
        "Return JSON with exactly these keys:\n"
        "- summary: concise combined profile summary tailored to interview prep\n"
        "- resume_summary: 4-6 bullet-style sentences summarising experience and strengths\n"
        "- jd_summary: 4-6 bullet-style sentences summarising role expectations\n"
        "- fit_highlights: array of 3-6 matching strengths\n"
        "- likely_gaps: array of 2-5 likely gaps or risks\n"
        "- focus_areas: array of 4-8 areas to emphasise when answering interview questions"
    )


def _coerce_paragraph_text(value) -> str:
    """
    Profile ORM stores resume_summary / jd_summary / summary as Text.
    LLMs often return bullet lists for those fields — SQLite cannot bind Python lists.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(x).strip() for x in value if x is not None and str(x).strip())
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _coerce_string_list(value) -> list[str]:
    """Ensure fit_highlights / likely_gaps / focus_areas are list[str] for JSON columns."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if x is not None and str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            pass
        return [s]
    return []


def format_summary_context(summary_data: dict) -> str:
    """Flatten summary fields into a plain-text block for LLM context injection."""
    parts = []
    if summary_data.get("summary"):
        parts.append(summary_data["summary"])
    highlights = summary_data.get("fit_highlights")
    if highlights:
        parts.append("Fit highlights: " + ", ".join(highlights))
    gaps = summary_data.get("likely_gaps")
    if gaps:
        parts.append("Likely gaps: " + ", ".join(gaps))
    focus = summary_data.get("focus_areas")
    if focus:
        parts.append("Focus areas: " + ", ".join(focus))
    return "\n\n".join(parts).strip()


def generate_profile_summary(
    name: str,
    role: str,
    resume_text: str,
    jd_text: str,
    additional_notes: str = "",
) -> dict:
    """Generate and return a structured summary dict via the configured LLM."""
    result = generate_json(
        _build_summary_prompt(name, role, resume_text, jd_text, additional_notes),
        system=_SUMMARY_SYSTEM,
        temperature=0.2,
        max_tokens=1200,
    )
    return {
        "summary": _coerce_paragraph_text(result.get("summary", "")),
        "resume_summary": _coerce_paragraph_text(result.get("resume_summary", "")),
        "jd_summary": _coerce_paragraph_text(result.get("jd_summary", "")),
        "fit_highlights": _coerce_string_list(result.get("fit_highlights")),
        "likely_gaps": _coerce_string_list(result.get("likely_gaps")),
        "focus_areas": _coerce_string_list(result.get("focus_areas")),
    }


def summarize_profile_async(
    profile_id: str,
    *,
    name: str,
    role: str,
    resume_text: str,
    jd_text: str,
    additional_notes: str = "",
) -> threading.Thread:
    """
    Fire a daemon thread to generate the profile summary without blocking the request.

    The thread writes the result (or an error status) back to the profile store
    so the frontend can poll /api/profile/<id> for completion.

    Phase 4 will replace this thread with a Celery task for better observability
    and retry behaviour.
    """
    # Capture the app object while we're still inside the request context.
    # The daemon thread runs after the request ends, so it needs its own
    # app context to access db.session.
    app = current_app._get_current_object()

    def _runner():
        with app.app_context():
            try:
                summary_data = generate_profile_summary(name, role, resume_text, jd_text, additional_notes)
                summary_data["summary_status"] = "complete"
                summary_data["summary_context"] = format_summary_context(summary_data)
                profile_repo.save(profile_id, summary_data)
                logger.info("Profile summary complete for profile_id=%s", profile_id)
            except Exception as exc:  # noqa: BLE001 — must not crash the daemon thread
                logger.error("Profile summary failed for profile_id=%s: %s", profile_id, exc)
                db.session.rollback()
                profile_repo.save(profile_id, {
                    "summary_status": "failed",
                    "summary_error": str(exc),
                })

    thread = threading.Thread(target=_runner, daemon=True, name=f"summary-{profile_id[:8]}")
    thread.start()
    return thread
