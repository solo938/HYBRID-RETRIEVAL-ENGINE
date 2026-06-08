"""Base abstraction for LLM providers."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        """Generate a response asynchronously."""
        pass

    @abstractmethod
    async def generate_async(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        """Generate a response asynchronously."""
        pass

    @abstractmethod
    async def stream_generate(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> AsyncIterator[str]:
        """Stream tokens as they are generated."""
        pass