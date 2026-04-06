"""
Profile repository — SQLAlchemy-backed data access layer.

Replaces the Phase 1 JSON file implementation with proper DB persistence.
The public interface (save / get / exists) is unchanged so no call site
in the service or API layers needed modification.

The Repository pattern keeps storage details here; the rest of the
application stays unaware of whether data lives in SQLite, MySQL, or
anything else — only the DATABASE_URL env var changes.
"""
import json
from datetime import datetime

from models.db import db
from models.profile import Profile

# ── Column name mapping ───────────────────────────────────────────────────────
# The dict key "profile_id" maps to the ORM column "id"; everything else
# is a direct match between the dict key and the model attribute name.
_DICT_TO_ATTR: dict[str, str] = {"profile_id": "id"}

# ORM Text columns — SQLite cannot bind Python lists; coerce lists to newline text.
_TEXT_ATTRS = frozenset(
    {
        "name",
        "email",
        "role",
        "company_name",
        "resume_text",
        "resume_filename",
        "jd_text",
        "jd_url",
        "additional_notes",
        "summary_status",
        "summary",
        "summary_context",
        "resume_summary",
        "jd_summary",
        "summary_error",
        "n8n_reason",
        "n8n_level",
    }
)


def _coerce_value_for_profile(key: str, value):
    if value is None:
        return None
    if key in _TEXT_ATTRS and isinstance(value, list):
        return "\n".join(str(x).strip() for x in value if x is not None and str(x).strip())
    if key in _TEXT_ATTRS and isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if key in ("fit_highlights", "likely_gaps", "focus_areas") and isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            return [s]
    return value


class ProfileRepository:
    """CRUD operations for Profile records via SQLAlchemy."""

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, profile_id: str, data: dict) -> dict:
        """
        Upsert *data* into the stored profile for *profile_id*.

        Creates the row if it does not exist; updates only the keys present
        in *data* if it does — so partial writes (e.g. writing only the
        summary fields after async generation) never clobber other columns.

        Returns the full profile as a dict after the write.
        """
        if not profile_id:
            profile_id = "anonymous"

        profile = db.session.get(Profile, profile_id)
        if profile is None:
            profile = Profile(id=profile_id, created_at=datetime.utcnow())
            db.session.add(profile)

        for key, value in data.items():
            if key == "profile_id":
                continue  # immutable after creation
            if hasattr(profile, key):
                coerced = _coerce_value_for_profile(key, value)
                if coerced is not None:
                    setattr(profile, key, coerced)

        profile.updated_at = datetime.utcnow()
        db.session.commit()
        return profile.to_dict()

    def get(self, profile_id: str) -> dict:
        """
        Fetch the stored profile for *profile_id*.

        Returns an empty dict if the profile does not exist, matching the
        old JSON behaviour so callers can do `if not profile_repo.get(id)`.
        """
        if not profile_id:
            return {}
        profile = db.session.get(Profile, profile_id)
        return profile.to_dict() if profile is not None else {}

    def exists(self, profile_id: str) -> bool:
        """Return True if *profile_id* has a stored row."""
        if not profile_id:
            return False
        return db.session.get(Profile, profile_id) is not None


# ── Module-level singleton ────────────────────────────────────────────────────
# Services and API handlers import this directly.
profile_repo = ProfileRepository()
