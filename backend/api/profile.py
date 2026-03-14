"""Profile orchestration endpoints for resume/JD prep flows."""
import os
import uuid

from flask import Blueprint, jsonify, request
from requests import RequestException

from models import get_profile_context, store_profile_context
from services.document_parser import extract_text_from_upload
from services.jd_fetcher import fetch_job_description
from services.n8n_client import post_webhook
from services.profile_summary import summarize_profile_async
from services.retriever import add_document

bp = Blueprint("profile", __name__)


def _pick_profile_id(payload: dict) -> str:
    return (
        payload.get("profile_id")
        or payload.get("user_id")
        or payload.get("email")
        or f"profile-{uuid.uuid4().hex[:12]}"
    )


def _parse_request_payload():
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        form = request.form.to_dict(flat=True)
        uploaded_file = request.files.get("resume_file")
        if uploaded_file and not form.get("resume_text"):
            form["resume_text"] = extract_text_from_upload(uploaded_file)
            form["resume_filename"] = uploaded_file.filename or "resume"
        return form
    return request.get_json() or {}


def _profile_context_text(profile: dict) -> str:
    summary = (profile.get("summary_context") or profile.get("summary") or "").strip()
    if summary:
        return summary

    parts = []
    resume_text = (profile.get("resume_text") or "").strip()
    jd_text = (profile.get("jd_text") or "").strip()
    if resume_text:
        parts.append(f"Resume:\n{resume_text[:3000]}")
    if jd_text:
        parts.append(f"Job Description:\n{jd_text[:3000]}")
    return "\n\n".join(parts)


@bp.route("/api/profile/init", methods=["POST"])
@bp.route("/api/prep-guide", methods=["POST"])
def init_profile_flow():
    payload = _parse_request_payload()
    resume_text = (payload.get("resume_text") or "").strip()
    jd_text = (payload.get("jd_text") or "").strip()
    jd_url = (payload.get("jd_url") or "").strip()

    if not resume_text:
        return jsonify({"error": "resume_text or resume_file is required"}), 400
    if not jd_text and not jd_url:
        return jsonify({"error": "Provide jd_text or jd_url"}), 400

    if jd_url and not jd_text:
        try:
            jd_text = fetch_job_description(jd_url)
        except (ValueError, RequestException) as e:
            return jsonify({"error": f"Failed to fetch JD URL: {str(e)}"}), 400

    profile_id = _pick_profile_id(payload)
    store_profile_context(profile_id, {
        "profile_id": profile_id,
        "name": payload.get("name", ""),
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
        "resume_text": resume_text,
        "jd_text": jd_text,
        "jd_url": jd_url,
        "additional_notes": payload.get("additional_notes", ""),
        "summary_status": "pending",
        "resume_filename": payload.get("resume_filename", ""),
    })

    # Index source documents so they remain available as additional retrieval context.
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

    webhook_url = os.getenv("N8N_FORM_WEBHOOK_URL", "").strip() or os.getenv("N8N_PREPAI_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return jsonify({"error": "Prep guide webhook not configured. Set N8N_FORM_WEBHOOK_URL."}), 503

    result = post_webhook(webhook_url, {
        "profile_id": profile_id,
        "name": payload.get("name", ""),
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
        "resume": resume_text,
        "jd_text": jd_text,
        "additional_notes": payload.get("additional_notes", ""),
    })
    return jsonify({
        "profile_id": profile_id,
        "summary_status": "pending",
        "message": result.get("message", "Detailed prep guide will be sent via email."),
    })


@bp.route("/api/profile/<profile_id>", methods=["GET"])
def get_profile(profile_id: str):
    profile = get_profile_context(profile_id)
    if not profile:
        return jsonify({"error": "profile not found"}), 404
    return jsonify({
        "profile_id": profile_id,
        "summary_status": profile.get("summary_status", "pending"),
        "summary": profile.get("summary", ""),
        "context": _profile_context_text(profile),
        "role": profile.get("role", ""),
        "email": profile.get("email", ""),
    })