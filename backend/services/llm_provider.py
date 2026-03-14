"""
AI Provider Abstraction Layer.
Implements a common interface for multiple LLM providers.
Use LLM_PROVIDER env var: mock | openai | anthropic | gemini
Default: mock (works offline, deterministic).
"""
import json
import os
import re
from abc import ABC, abstractmethod

# Lazy imports for providers - only load when needed
_openai_client = None
_anthropic_client = None
_gemini_model = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _openai_client


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    return _anthropic_client


def _get_gemini():
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        _gemini_model = genai.GenerativeModel(os.getenv("LLM_MODEL", "gemini-pro"))
    return _gemini_model


def _parse_json_from_text(text: str) -> dict:
    """Extract JSON object from model output, handling markdown code blocks."""
    text = text.strip()
    # Try to find JSON in ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    # Fallback: find first { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "improvements": [], "confidence": 0.5, "sources": []}


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class MockProvider(BaseLLMProvider):
    """
    Deterministic mock provider for offline demo.
    Returns fixed structure so UI always works.
    """

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        # Detect which template was used and return appropriate JSON
        if "candidate_answer" in prompt.lower():
            return json.dumps({
                "score": 7.5,
                "rationale": "Good foundational understanding. Covered key concepts.",
                "improvements": ["Add more concrete examples", "Mention HTTP status codes", "Discuss versioning"],
                "confidence": 0.85
            })
        if "resume_text" in prompt.lower() or "job description" in prompt.lower():
            return json.dumps({
                "strengths": ["Python experience", "API development", "Database skills"],
                "weaknesses": ["Limited cloud experience", "No Kubernetes background"],
                "key_topics": ["System design", "Distributed systems", "Kubernetes", "AWS"],
                "practice_questions": [
                    "Design a URL shortener",
                    "Explain CAP theorem",
                    "Describe your microservices experience"
                ],
                "study_plan": [
                    "Week 1: System design basics",
                    "Week 2: Cloud fundamentals (AWS)",
                    "Week 3: Kubernetes concepts",
                    "Week 4: Mock interviews"
                ]
            })
        return json.dumps({
            "answer": "Here is a strong answer: Focus on clarity, structure (STAR format), and relevance to the question. Be concise but thorough.",
            "improvements": ["Use the STAR method", "Add a concrete example", "Tie back to the job requirements"],
            "confidence": 0.9,
            "sources": []
        })

    @property
    def name(self) -> str:
        return "mock"


class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        client = _get_openai()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content or ""

    @property
    def name(self) -> str:
        return "openai"


class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        client = _get_anthropic()
        r = client.messages.create(
            model=os.getenv("LLM_MODEL", "claude-3-sonnet-20240229"),
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
    def generate(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        model = _get_gemini()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        r = model.generate_content(
            full_prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return r.text if r.text else ""

    @property
    def name(self) -> str:
        return "gemini"


_PROVIDERS = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}


def get_provider() -> BaseLLMProvider:
    """Factory: returns provider based on LLM_PROVIDER env."""
    name = (os.getenv("LLM_PROVIDER") or "mock").lower()
    if name not in _PROVIDERS:
        return MockProvider()
    return _PROVIDERS[name]()


def generate_json(prompt: str, system: str = "", **kwargs) -> dict:
    """Convenience: generate and parse JSON response."""
    provider = get_provider()
    raw = provider.generate(prompt, system=system, **kwargs)
    return _parse_json_from_text(raw)
