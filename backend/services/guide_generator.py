"""
Instant Guide generator — produces a full interview prep guide in-process.

Used when the user selects "Instant Guide" mode (no n8n/email required).
Calls the configured LLM once with a structured prompt that both classifies
the candidate's seniority and generates the personalised guide in one shot.

The guide is returned as a markdown string; the frontend renders it directly.
"""
import logging

from config import Config
from services.llm import get_provider

logger = logging.getLogger("prepai")

_SYSTEM = (
    "You are an expert interview coach and technical mentor. "
    "You will analyze a candidate's profile and generate a comprehensive, "
    "personalized interview preparation guide.\n\n"
    "IMPORTANT — your very first line of output must be exactly one of:\n"
    "LEVEL: fresher\n"
    "LEVEL: mid_level\n"
    "LEVEL: senior\n\n"
    "Seniority guide: fresher = 0–2 years, mid_level = 2–5 years, senior = 5+ years.\n"
    "After that line, output the full prep guide in clean Markdown."
)


def _build_prompt(
    name: str,
    role: str,
    company_name: str,
    resume_text: str,
    jd_text: str,
    additional_notes: str,
) -> str:
    return (
        f"Candidate: {name}\n"
        f"Target Role: {role}\n"
        f"Company: {company_name}\n\n"
        f"Resume:\n{resume_text[:Config.SUMMARY_RESUME_MAX_CHARS]}\n\n"
        f"Job Description:\n{jd_text[:Config.SUMMARY_JD_MAX_CHARS]}\n\n"
        f"Additional Notes:\n{additional_notes}\n\n"
        "Generate a comprehensive, actionable interview prep guide with these sections:\n"
        "## Role Analysis\n"
        "## Key Technical Areas to Study (include one resource link per topic)\n"
        "## Mock Interview Questions\n"
        "### Technical Questions (8–12 questions)\n"
        "### Behavioral Questions (4–5 questions with STAR tips)\n"
        "## 7-Day Study Plan\n"
        "## Quick Wins & Tips\n\n"
        "Be specific — reference the actual role, company, and candidate background throughout."
    )


def generate_instant_guide(
    name: str,
    role: str,
    company_name: str,
    resume_text: str,
    jd_text: str,
    additional_notes: str = "",
) -> dict:
    """
    Generate a personalised prep guide and return it as a dict:
        {
            "guide":  str,   # full markdown guide
            "level":  str,   # "fresher" | "mid_level" | "senior"
        }

    Falls back gracefully if the LLM fails to include the LEVEL header.
    """
    provider = get_provider()
    prompt = _build_prompt(name, role, company_name, resume_text, jd_text, additional_notes)

    raw = provider.generate(
        prompt,
        system=_SYSTEM,
        temperature=0.4,
        max_tokens=2500,
    )

    # Parse the mandatory first line: "LEVEL: mid_level"
    lines = raw.strip().splitlines()
    level = "mid_level"  # safe default
    guide = raw.strip()

    if lines and lines[0].upper().startswith("LEVEL:"):
        raw_level = lines[0].split(":", 1)[1].strip().lower()
        if raw_level in {"fresher", "mid_level", "senior"}:
            level = raw_level
        # Strip the LEVEL line from the guide the user sees
        guide = "\n".join(lines[1:]).strip()

    logger.info("Instant guide generated | level=%s | chars=%d", level, len(guide))
    return {"guide": guide, "level": level}
