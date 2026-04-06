"""
Profile orchestration endpoints.

POST /api/prep-guide  (alias: /api/profile/init)
    Accepts a resume + job description, stores the profile, kicks off async
    summarisation, then branches on `mode`:

    mode="instant"  (default)
        Generates the prep guide in-process via the configured LLM and
        returns it in the response body as markdown. No email is sent.
        Email field is optional.

    mode="n8n"
        Fires the n8n webhook which qualifies the candidate, classifies
        seniority, and emails a personalised guide. Requires
        N8N_PREPAI_WEBHOOK_URL to be configured.

GET  /api/profile/<profile_id>
    Returns stored profile metadata and summary status for the Ask page.
"""
import logging
import os
import uuid

from flask import Blueprint, jsonify, request
from requests import RequestException

from config import Config
from repositories import profile_repo
from services.document_parser import extract_text_from_upload
from services.guide_generator import generate_instant_guide
from services.jd_fetcher import (
    extract_company_name_from_jd_text,
    extract_company_name_from_url,
    fetch_job_description,
)
from services.n8n_client import post_webhook
from services.profile_summary import summarize_profile_async
from services.retriever import add_document

logger = logging.getLogger("prepai")
bp = Blueprint("profile", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_profile_id(payload: dict) -> str:
    """Return an explicit profile_id from the payload or generate a unique one."""
    return (
        payload.get("profile_id")
        or payload.get("user_id")
        or f"profile-{uuid.uuid4().hex[:12]}"
    )


def _parse_request_payload() -> dict:
    """
    Parse the incoming request into a unified dict regardless of content type.
    Multipart form data (file upload) and JSON are both supported.
    Raises ValueError if the uploaded file is invalid.
    """
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        form = request.form.to_dict(flat=True)
        uploaded_file = request.files.get("resume_file")
        if uploaded_file and uploaded_file.filename:
            form["resume_text"] = extract_text_from_upload(uploaded_file)
            form["resume_filename"] = uploaded_file.filename
        return form
    return request.get_json(silent=True) or {}


def _build_profile_context_text(profile: dict) -> str:
    """Build the plain-text context block for the Ask page."""
    summary = (profile.get("summary_context") or profile.get("summary") or "").strip()
    if summary:
        return summary

    parts = []
    resume = (profile.get("resume_text") or "").strip()
    jd = (profile.get("jd_text") or "").strip()
    if resume:
        parts.append(f"Resume:\n{resume[:Config.SUMMARY_RESUME_MAX_CHARS]}")
    if jd:
        parts.append(f"Job Description:\n{jd[:Config.SUMMARY_JD_MAX_CHARS]}")
    return "\n\n".join(parts)


# ── Shared setup (both modes) ─────────────────────────────────────────────────

def _setup_profile(payload: dict) -> tuple[str, str, str, str, str]:
    """
    Validate inputs, fetch JD if needed, infer company name, save to DB,
    index chunks, and kick off async summarisation.

    Returns (profile_id, resume_text, jd_text, jd_url, company_name).
    Raises ValueError on bad input, RequestException on URL fetch failure.
    """
    resume_text = (payload.get("resume_text") or "").strip()
    jd_text = (payload.get("jd_text") or "").strip()
    jd_url = (payload.get("jd_url") or "").strip()

    if not resume_text:
        raise ValueError("Provide your resume as a file upload or pasted text.")
    if not jd_text and not jd_url:
        raise ValueError("Provide the job description as a URL or pasted text.")

    if jd_url and not jd_text:
        jd_text = fetch_job_description(jd_url)

    company_name = extract_company_name_from_url(jd_url) if jd_url else "Company"
    if company_name == "Company" and jd_text:
        company_name = extract_company_name_from_jd_text(jd_text)

    profile_id = _generate_profile_id(payload)

    profile_repo.save(profile_id, {
        "profile_id": profile_id,
        "name": payload.get("name", ""),
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
        "company_name": company_name,
        "resume_text": resume_text,
        "jd_text": jd_text,
        "jd_url": jd_url,
        "additional_notes": payload.get("additional_notes", ""),
        "resume_filename": payload.get("resume_filename", ""),
        "summary_status": "pending",
    })

    add_document(f"{profile_id}_resume", resume_text, metadata={"profile_id": profile_id, "source": "resume"})
    add_document(f"{profile_id}_jd", jd_text, metadata={"profile_id": profile_id, "source": "jd"})

    summarize_profile_async(
        profile_id,
        name=payload.get("name", ""),
        role=payload.get("role", ""),
        resume_text=resume_text,
        jd_text=jd_text,
        additional_notes=payload.get("additional_notes", ""),
    )

    return profile_id, resume_text, jd_text, jd_url, company_name


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/api/profile/init", methods=["POST"])
@bp.route("/api/prep-guide", methods=["POST"])
def init_profile_flow():
    """
    Submit a new prep-guide profile.

    Required: resume_text (or resume_file), and one of jd_text / jd_url.
    Optional: name, email (required for n8n mode), role, additional_notes.
    Optional: mode = "instant" (default) | "n8n"
    """
    try:
        payload = _parse_request_payload()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    mode = (payload.get("mode") or "instant").strip().lower()

    # ── Common: validate, save, index, start async summary ────────────────────
    try:
        profile_id, resume_text, jd_text, jd_url, company_name = _setup_profile(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RequestException as exc:
        return jsonify({"error": f"Could not fetch the job description URL: {exc}"}), 400

    # ── Instant Guide mode ────────────────────────────────────────────────────
    if mode == "instant":
        try:
            result = generate_instant_guide(
                name=payload.get("name", ""),
                role=payload.get("role", ""),
                company_name=company_name,
                resume_text=resume_text,
                jd_text=jd_text,
                additional_notes=payload.get("additional_notes", ""),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Instant guide generation failed: %s", exc)
            return jsonify({"error": "Guide generation failed. Please try again."}), 500

        return jsonify({
            "profile_id": profile_id,
            "company_name": company_name,
            "summary_status": "pending",
            "mode": "instant",
            "guide": result["guide"],
            "level": result["level"],
            "message": "Your prep guide is ready below. Open Ask to get personalised answers for this role.",
        })

    # ── n8n Email mode ────────────────────────────────────────────────────────
    webhook_url = (
        os.getenv("N8N_PREPAI_WEBHOOK_URL", "").strip()
        or os.getenv("N8N_FORM_WEBHOOK_URL", "").strip()
    )
    if not webhook_url:
        logger.error("N8N_PREPAI_WEBHOOK_URL not configured — skipping webhook")
        return jsonify({
            "error": (
                "Email delivery is not configured (N8N_PREPAI_WEBHOOK_URL is missing). "
                "Switch to Instant Guide mode to generate your prep guide on-screen instead."
            )
        }), 503

    n8n_payload = {
        "profile_id": profile_id,
        "Your name": payload.get("name", ""),
        "Email": payload.get("email", ""),
        "Role you're applying for": payload.get("role", ""),
        "Resume text": resume_text,
        "Job description URL": jd_url or "",
        "Or paste job description text": jd_text if not jd_url else "",
        "Additional notes": payload.get("additional_notes", ""),
    }

    n8n_result = {}
    try:
        n8n_result = post_webhook(webhook_url, n8n_payload)
    except (RequestException, ValueError) as exc:
        logger.warning("n8n webhook call failed (profile saved): %s", exc)

    return jsonify({
        "profile_id": profile_id,
        "company_name": company_name,
        "summary_status": "pending",
        "mode": "n8n",
        "message": n8n_result.get(
            "message",
            "Your personalised prep guide will be emailed shortly. "
            "You can use Ask now to get personalised answers for this role.",
        ),
    })


@bp.route("/api/profile/<profile_id>", methods=["GET"])
def get_profile(profile_id: str):
    """Return profile metadata and summary status for the Ask page selector."""
    profile = profile_repo.get(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify({
        "profile_id": profile_id,
        "company_name": profile.get("company_name", ""),
        "summary_status": profile.get("summary_status", "pending"),
        "summary": profile.get("summary", ""),
        "context": _build_profile_context_text(profile),
        "role": profile.get("role", ""),
        "email": profile.get("email", ""),
        "n8n_qualified": profile.get("n8n_qualified"),
        "n8n_level": profile.get("n8n_level"),
        "resume_summary": profile.get("resume_summary", ""),
        "jd_summary": profile.get("jd_summary", ""),
        "fit_highlights": profile.get("fit_highlights", []),
        "likely_gaps": profile.get("likely_gaps", []),
        "focus_areas": profile.get("focus_areas", []),
    })
