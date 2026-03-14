"""Profile summary generation using the configured local LLM provider."""
import threading

from models import store_profile_context
from services.llm_provider import generate_json


SUMMARY_SYSTEM = (
    "You are an interview preparation analyst. Summarize a candidate profile and target role "
    "for later personalized interview coaching. Return only valid JSON."
)


def _summary_prompt(name: str, role: str, resume_text: str, jd_text: str, additional_notes: str) -> str:
    return f"""
Candidate name: {name}
Target role: {role}
Resume:
{resume_text}

Job description:
{jd_text}

Additional notes:
{additional_notes}

Return JSON with exactly these keys:
- summary: concise combined profile summary tailored to interview prep
- resume_summary: 4-6 bullet-style sentences summarizing experience and strengths
- jd_summary: 4-6 bullet-style sentences summarizing role expectations
- fit_highlights: array of 3-6 matching strengths
- likely_gaps: array of 2-5 likely gaps or risks
- focus_areas: array of 4-8 areas to emphasize while answering interview questions
""".strip()


def format_summary_context(summary_data: dict) -> str:
    parts = []
    if summary_data.get("summary"):
        parts.append(summary_data["summary"])
    if summary_data.get("fit_highlights"):
        parts.append("Fit highlights: " + ", ".join(summary_data.get("fit_highlights", [])))
    if summary_data.get("likely_gaps"):
        parts.append("Likely gaps: " + ", ".join(summary_data.get("likely_gaps", [])))
    if summary_data.get("focus_areas"):
        parts.append("Focus areas: " + ", ".join(summary_data.get("focus_areas", [])))
    return "\n\n".join(parts).strip()


def generate_profile_summary(name: str, role: str, resume_text: str, jd_text: str, additional_notes: str = "") -> dict:
    result = generate_json(
        _summary_prompt(name, role, resume_text, jd_text, additional_notes),
        system=SUMMARY_SYSTEM,
        temperature=0.2,
        max_tokens=1200,
    )

    return {
        "summary": result.get("summary", ""),
        "resume_summary": result.get("resume_summary", ""),
        "jd_summary": result.get("jd_summary", ""),
        "fit_highlights": result.get("fit_highlights", []) if isinstance(result.get("fit_highlights"), list) else [],
        "likely_gaps": result.get("likely_gaps", []) if isinstance(result.get("likely_gaps"), list) else [],
        "focus_areas": result.get("focus_areas", []) if isinstance(result.get("focus_areas"), list) else [],
    }


def summarize_profile_async(profile_id: str, *, name: str, role: str, resume_text: str, jd_text: str, additional_notes: str = ""):
    def _runner():
        try:
            summary_data = generate_profile_summary(name, role, resume_text, jd_text, additional_notes)
            summary_data["summary_status"] = "complete"
            summary_data["summary_context"] = format_summary_context(summary_data)
            store_profile_context(profile_id, summary_data)
        except (ValueError, RuntimeError, TypeError, OSError) as exc:
            store_profile_context(profile_id, {
                "summary_status": "failed",
                "summary_error": str(exc),
            })

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return thread