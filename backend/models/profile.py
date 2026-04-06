"""
SQLAlchemy ORM model for a PrepAI candidate profile.

Maps to the `profiles` table. All text fields default to empty string so
partial upserts (e.g. writing only the summary after async generation) never
produce NULL columns. The nullable boolean fields (n8n_qualified, n8n_email_sent)
are intentionally nullable — NULL means "not yet determined".

to_dict() returns the flat dict that the service and API layers already expect,
keeping the repository interface identical to the old JSON-backed version.
"""
from datetime import datetime

from models.db import db


class Profile(db.Model):
    __tablename__ = "profiles"

    # ── Identity ─────────────────────────────────────────────────────────────
    id = db.Column(db.String(64), primary_key=True)          # profile_id
    name = db.Column(db.String(255), nullable=False, default="")
    email = db.Column(db.String(255), nullable=False, default="")
    role = db.Column(db.String(255), nullable=False, default="")
    company_name = db.Column(db.String(255), nullable=False, default="")

    # ── Source documents ──────────────────────────────────────────────────────
    resume_text = db.Column(db.Text, nullable=False, default="")
    resume_filename = db.Column(db.String(500), nullable=False, default="")
    jd_text = db.Column(db.Text, nullable=False, default="")
    jd_url = db.Column(db.String(500), nullable=False, default="")
    additional_notes = db.Column(db.Text, nullable=False, default="")

    # ── AI-generated summary (written by async thread) ────────────────────────
    summary_status = db.Column(db.String(20), nullable=False, default="pending")
    summary = db.Column(db.Text, nullable=False, default="")
    summary_context = db.Column(db.Text, nullable=False, default="")
    resume_summary = db.Column(db.Text, nullable=False, default="")
    jd_summary = db.Column(db.Text, nullable=False, default="")
    fit_highlights = db.Column(db.JSON, nullable=False, default=list)
    likely_gaps = db.Column(db.JSON, nullable=False, default=list)
    focus_areas = db.Column(db.JSON, nullable=False, default=list)
    summary_error = db.Column(db.Text, nullable=False, default="")

    # ── n8n workflow outcome (written by /api/webhook/result callback) ────────
    n8n_qualified = db.Column(db.Boolean, nullable=True)
    n8n_reason = db.Column(db.Text, nullable=False, default="")
    n8n_email_sent = db.Column(db.Boolean, nullable=True)
    n8n_level = db.Column(db.String(20), nullable=False, default="")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    chunks = db.relationship(
        "Chunk",
        backref="profile",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """
        Return a plain dict matching the shape the rest of the app expects.

        Uses the same key names as the old JSON store so every call site
        (API handlers, profile_summary, etc.) works without changes.
        """
        return {
            "profile_id": self.id,
            "name": self.name or "",
            "email": self.email or "",
            "role": self.role or "",
            "company_name": self.company_name or "",
            "resume_text": self.resume_text or "",
            "resume_filename": self.resume_filename or "",
            "jd_text": self.jd_text or "",
            "jd_url": self.jd_url or "",
            "additional_notes": self.additional_notes or "",
            "summary_status": self.summary_status or "pending",
            "summary": self.summary or "",
            "summary_context": self.summary_context or "",
            "resume_summary": self.resume_summary or "",
            "jd_summary": self.jd_summary or "",
            "fit_highlights": self.fit_highlights or [],
            "likely_gaps": self.likely_gaps or [],
            "focus_areas": self.focus_areas or [],
            "summary_error": self.summary_error or "",
            "n8n_qualified": self.n8n_qualified,
            "n8n_reason": self.n8n_reason or "",
            "n8n_email_sent": self.n8n_email_sent,
            "n8n_level": self.n8n_level or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }

    def __repr__(self) -> str:
        return f"<Profile id={self.id!r} role={self.role!r} status={self.summary_status!r}>"
