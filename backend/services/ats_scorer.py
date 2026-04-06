"""
ATS (Applicant Tracking System) compatibility scorer.

Compares a candidate's resume against a job description to produce:
  - A numerical fit score (0–100)
  - Matched keywords / skills
  - Missing keywords the candidate should add
  - Actionable suggestions to improve the resume

Uses a structured LLM call so the analysis is contextual, not just
keyword-counting.
"""
import logging

from config import Config
from services.llm import generate_json, get_provider

logger = logging.getLogger("prepai")

_SYSTEM = (
    "You are an expert ATS (Applicant Tracking System) analyst and resume coach. "
    "Analyse a resume against a job description and return a structured compatibility report."
)

_PROMPT = """\
Resume:
{resume_text}

Job Description:
{jd_text}

Analyse how well this resume matches the job description.
Return a JSON object with exactly these keys:
- score: integer 0–100 representing overall ATS compatibility
- matched_keywords: array of skills/technologies/qualifications found in BOTH the resume and JD
- missing_keywords: array of important skills/qualifications required by the JD but NOT found in the resume
- category_scores: object with keys "skills" (0–100), "experience" (0–100), "education" (0–100), "keywords" (0–100)
- suggestions: array of 3–5 specific, actionable improvements the candidate should make to their resume for this role
- summary: one-paragraph assessment of the candidate's fit for this role
"""


def compute_ats_score(resume_text: str, jd_text: str) -> dict:
    """
    Run an LLM-based ATS analysis of *resume_text* against *jd_text*.

    Returns a dict with score, matched/missing keywords, category scores,
    suggestions, and a summary paragraph.
    """
    prompt = _PROMPT.format(
        resume_text=resume_text[:Config.RESUME_MAX_CHARS],
        jd_text=jd_text[:Config.JD_MAX_CHARS],
    )

    result = generate_json(
        prompt,
        system=_SYSTEM,
        temperature=0.2,
        max_tokens=1200,
    )

    score = result.get("score", 0)
    if isinstance(score, str):
        try:
            score = int(score)
        except ValueError:
            score = 0
    score = max(0, min(100, score))

    matched = result.get("matched_keywords", [])
    if isinstance(matched, str):
        matched = [s.strip() for s in matched.split(",") if s.strip()]

    missing = result.get("missing_keywords", [])
    if isinstance(missing, str):
        missing = [s.strip() for s in missing.split(",") if s.strip()]

    suggestions = result.get("suggestions", [])
    if isinstance(suggestions, str):
        suggestions = [suggestions] if suggestions.strip() else []

    category_scores = result.get("category_scores", {})
    if not isinstance(category_scores, dict):
        category_scores = {}
    for key in ("skills", "experience", "education", "keywords"):
        val = category_scores.get(key, 0)
        if isinstance(val, str):
            try:
                val = int(val)
            except ValueError:
                val = 0
        category_scores[key] = max(0, min(100, val))

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "category_scores": category_scores,
        "suggestions": suggestions,
        "summary": str(result.get("summary", "")),
    }
