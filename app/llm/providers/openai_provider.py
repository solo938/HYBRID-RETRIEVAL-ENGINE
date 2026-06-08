"""OpenAI LLM provider."""
import openai
from typing import AsyncIterator
from app.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):  # Changed from gpt-4-turbo-preview
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        """Generate a response asynchronously."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def generate_async(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        """Alias for generate."""
        return await self.generate(prompt, max_tokens, temperature)

    async def stream_generate(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content