"""
Prompt templates for PrepAI LLM calls.
Centralises all prompt strings so they are easy to iterate on without
touching business logic in the API layer.
"""

# ── /api/ask ─────────────────────────────────────────────────────────────────

ASK_SYSTEM = (
    "You are an expert interview preparation assistant. "
    "Help the candidate understand the question and give a strong, structured answer "
    "tailored to their background and the target role."
)

ASK_USER = """\
Candidate context (resume + job description — use this to personalise the answer):
{retrieved_context}

Interview question:
{question}

Return a JSON object with exactly these keys:
- answer: A clear, concise answer tailored to the candidate's background and the role
- improvements: List of 1-3 specific improvements or follow-up talking points
- confidence: Float 0.0–1.0 indicating confidence in the answer quality
- sources: List of source labels from context used (empty list if no context was used)
"""


def build_ask_prompt(question: str, retrieved_context: str = "") -> tuple[str, str]:
    """
    Build the (system, user) message pair for /api/ask.

    Args:
        question: The interview question submitted by the user.
        retrieved_context: Resume + JD context or RAG chunks (may be empty).

    Returns:
        (system_message, user_message) tuple ready for LLM consumption.
    """
    context = retrieved_context.strip() or "(No profile context provided)"
    user_msg = ASK_USER.format(retrieved_context=context, question=question)
    return ASK_SYSTEM, user_msg
