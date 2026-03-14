"""
Reusable prompt templates for PrepAI.
Centralizes prompt engineering for Ask, Evaluate, and Prep flows.
"""

# -----------------------------------------------------------------------------
# ASK TEMPLATE - Interview Q&A with context
# -----------------------------------------------------------------------------
ASK_SYSTEM = """You are an expert interview preparation assistant. Help the candidate understand the question and give a strong, structured answer."""

ASK_USER = """Context (retrieved from knowledge base, may be empty):
{retrieved_context}

Question:
{question}

Provide a JSON response with exactly these keys:
- answer: A clear, concise answer to the question
- improvements: List of 1-3 specific improvements or follow-up points
- confidence: Float 0-1 indicating confidence in the answer
- sources: List of source identifiers from context (empty if no context used)
"""

# -----------------------------------------------------------------------------
# EVALUATE TEMPLATE - Score candidate answer
# -----------------------------------------------------------------------------
EVAL_SYSTEM = """You are an expert technical interviewer. Evaluate the candidate's answer objectively."""

EVAL_USER = """Question asked:
{question}

Candidate's answer:
{candidate_answer}

Provide a JSON response with exactly these keys:
- score: Float 0-10
- rationale: Brief explanation of the score
- improvements: List of 2-4 specific improvements
- confidence: Float 0-1
"""

# -----------------------------------------------------------------------------
# PREP ROADMAP TEMPLATE - Resume + JD → study plan
# -----------------------------------------------------------------------------
PREP_SYSTEM = """You are a career coach. Analyze the resume against the job description and create a preparation roadmap."""

PREP_USER = """Resume:
{resume_text}

Job Description:
{jd_text}

Provide a JSON response with exactly these keys:
- strengths: List of 3-5 strengths that match the JD
- weaknesses: List of 2-4 gaps or weaknesses to address
- key_topics: List of 5-8 key topics to study
- practice_questions: List of 5-7 interview questions to practice
- study_plan: List of 4-6 actionable study steps
"""


def build_ask_prompt(question: str, retrieved_context: str = "") -> tuple[str, str]:
    """Build (system, user) prompt for /api/ask."""
    context = retrieved_context.strip() or "(No additional context)"
    user = ASK_USER.format(retrieved_context=context, question=question)
    return ASK_SYSTEM, user


def build_evaluate_prompt(question: str, candidate_answer: str) -> tuple[str, str]:
    """Build (system, user) prompt for /api/evaluate."""
    user = EVAL_USER.format(question=question, candidate_answer=candidate_answer)
    return EVAL_SYSTEM, user


def build_prep_prompt(resume_text: str, jd_text: str) -> tuple[str, str]:
    """Build (system, user) prompt for /api/prepare."""
    user = PREP_USER.format(resume_text=resume_text, jd_text=jd_text)
    return PREP_SYSTEM, user
