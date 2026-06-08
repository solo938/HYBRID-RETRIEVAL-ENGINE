"""Local LLM provider using Ollama (completely free)."""
import json
from typing import AsyncIterator
import aiohttp
from app.llm.base import BaseLLMProvider


class LocalLLMProvider(BaseLLMProvider):
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    }
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                result = await resp.json()
                return result.get("response", "")

    async def generate_async(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1) -> str:
        return await self.generate(prompt, max_tokens, temperature)

    async def stream_generate(
        self, prompt: str, max_tokens: int = 1024, temperature: float = 0.1
    ) -> AsyncIterator[str]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    }
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except:
                            pass