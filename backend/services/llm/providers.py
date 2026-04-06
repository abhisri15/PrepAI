"""
Concrete LLM provider implementations.

Each class wraps one AI provider's SDK behind the BaseLLMProvider interface.
Client objects are initialised once in __init__ (the factory caches instances),
so there is no module-level global state and no thread-safety concern here.
"""
import json
import os

from config import Config
from services.llm.base import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """
    Deterministic offline mock — no API key required.

    Returns plausible JSON so the UI and test suite work without live keys.
    Useful for local development and CI environments.
    """

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        sys_lower = system.lower()
        if "summarize" in sys_lower or "summarise" in sys_lower or "summary" in sys_lower or "analyst" in sys_lower:
            return json.dumps({
                "summary": "Strong Python/Flask engineer targeting this role.",
                "fit_highlights": ["Python experience", "API development"],
                "likely_gaps": ["Limited cloud exposure"],
                "focus_areas": ["System design", "Distributed systems"],
            })
        if "prep guide" in sys_lower or "preparation guide" in sys_lower or "level:" in sys_lower:
            return (
                "LEVEL: mid_level\n\n"
                "## Your Personalised Prep Guide\n\n"
                "### Key Focus Areas\n- System design fundamentals\n- API design best practices\n\n"
                "### Likely Interview Topics\n- Python internals\n- REST API design\n\n"
                "### Tips\nBe concise and use concrete examples from your experience."
            )
        return json.dumps({
            "answer": "Focus on clarity, structure (STAR format), and relevance. Be concise but thorough.",
            "improvements": ["Use STAR method", "Add a concrete example", "Tie back to role requirements"],
            "confidence": 0.9,
            "sources": [],
        })

    @property
    def name(self) -> str:
        return "mock"


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = self._client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content or ""

    @property
    def name(self) -> str:
        return "openai"


class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        r = self._client.messages.create(
            model=os.getenv("LLM_MODEL", "claude-3-5-haiku-20241022"),
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return r.content[0].text if r.content else ""

    @property
    def name(self) -> str:
        return "anthropic"


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        self._model = genai.GenerativeModel(os.getenv("LLM_MODEL", "gemini-1.5-flash"))

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        r = self._model.generate_content(
            full_prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return r.text if r.text else ""

    @property
    def name(self) -> str:
        return "gemini"


class GroqProvider(BaseLLMProvider):
    """Groq (OpenAI-compatible API) — preferred for /api/ask due to fast inference."""

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = self._client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (r.choices[0].message.content or "").strip()

    @property
    def name(self) -> str:
        return "groq"
