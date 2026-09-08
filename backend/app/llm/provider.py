from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from app.config import Settings

logger = logging.getLogger("craftify.llm")

STUB_MESSAGE = (
    "[stub] DeepSeek is not configured. Retrieved context was still produced; "
    "set DEEPSEEK_API_KEY and restart to generate a real answer."
)


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        raise NotImplementedError


class StubProvider(LLMProvider):
    name = "stub"

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        return STUB_MESSAGE


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        url = self.settings.deepseek_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.settings.deepseek_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def get_provider(settings: Settings) -> LLMProvider:
    if not settings.deepseek_configured:
        logger.warning("DEEPSEEK_API_KEY is unset — using stub LLM provider")
        return StubProvider()
    return DeepSeekProvider(settings)
