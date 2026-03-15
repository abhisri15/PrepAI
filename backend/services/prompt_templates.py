"""
Reusable prompt templates for PrepAI.
Used by /api/ask for interview Q&A with profile context.
"""

ASK_SYSTEM = """You are an expert interview preparation assistant. Help the candidate understand the question and give a strong, structured answer."""

ASK_USER = """Context (candidate's resume and job description summary; use this to personalize the answer):
{retrieved_context}

Question:
{question}

Provide a JSON response with exactly these keys:
- answer: A clear, concise answer tailored to the candidate's background and the role
- improvements: List of 1-3 specific improvements or follow-up points
- confidence: Float 0-1 indicating confidence in the answer
- sources: List of source identifiers from context (empty if no context used)
"""


def build_ask_prompt(question: str, retrieved_context: str = "") -> tuple[str, str]:
    """Build (system, user) prompt for /api/ask."""
    context = retrieved_context.strip() or "(No additional context)"
    user = ASK_USER.format(retrieved_context=context, question=question)
    return ASK_SYSTEM, user
