"""
Abstract base class for all LLM providers (Strategy interface).

Every concrete provider implements generate() so the rest of the
application can swap models without changing call sites.
"""
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Strategy interface for LLM text generation."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Send *prompt* to the model and return the raw text response."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs and health checks (e.g. 'groq', 'mock')."""
