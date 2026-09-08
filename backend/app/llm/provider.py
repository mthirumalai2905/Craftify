from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.config import Settings

logger = logging.getLogger("craftify.llm")

STUB_MESSAGE = (
    "[stub] DeepSeek is not configured. Retrieved context was still produced; "
    "set DEEPSEEK_API_KEY and restart to generate a real answer."
)

# Official DeepSeek list prices as of 2026-09-09 from
# https://api-docs.deepseek.com/quick_start/pricing/
# `deepseek-chat` aliases to deepseek-v4-flash (non-thinking).
# Figures are USD per 1M tokens. Off-peak is half of peak.
# Peak hours: 01:00–04:00 and 06:00–10:00 UTC, Monday–Friday.
# This is an estimate: we price all prompt tokens at the cache-miss rate
# (cache hits are cheaper) and pick peak vs off-peak from the current UTC clock.
_FLASH_INPUT_PER_M_PEAK = 0.44
_FLASH_INPUT_PER_M_OFFPEAK = 0.22
_FLASH_OUTPUT_PER_M_PEAK = 1.32
_FLASH_OUTPUT_PER_M_OFFPEAK = 0.66


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def _is_peak(now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return (60 <= minutes < 240) or (360 <= minutes < 600)


def estimated_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Approximate USD cost from official Flash cache-miss rates. Estimate only."""
    if _is_peak():
        input_rate, output_rate = _FLASH_INPUT_PER_M_PEAK, _FLASH_OUTPUT_PER_M_PEAK
    else:
        input_rate, output_rate = _FLASH_INPUT_PER_M_OFFPEAK, _FLASH_OUTPUT_PER_M_OFFPEAK
    cost = (prompt_tokens / 1_000_000) * input_rate + (completion_tokens / 1_000_000) * output_rate
    return round(cost, 6)


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.1) -> LLMResult:
        raise NotImplementedError


class StubProvider(LLMProvider):
    name = "stub"

    def generate(self, system: str, user: str, temperature: float = 0.1) -> LLMResult:
        return LLMResult(text=STUB_MESSAGE, prompt_tokens=0, completion_tokens=0, total_tokens=0)


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, system: str, user: str, temperature: float = 0.1) -> LLMResult:
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
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return LLMResult(
            text=data["choices"][0]["message"]["content"].strip(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )


def get_provider(settings: Settings) -> LLMProvider:
    if not settings.deepseek_configured:
        logger.warning("DEEPSEEK_API_KEY is unset — using stub LLM provider")
        return StubProvider()
    return DeepSeekProvider(settings)
