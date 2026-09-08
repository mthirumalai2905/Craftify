from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.agent.tools import infer_priority
from app.llm.provider import LLMProvider, LLMResult, StubProvider
from app.prompts.agent_prompt import AGENT_SYSTEM_PROMPT

TICKET_RE = re.compile(
    r"\b(?:create|file|open|submit|raise|make)\b.{0,40}\b(?:support\s+)?ticket\b"
    r"|\b(?:i want to|i'd like to|i would like to|please)\b.{0,30}\b(?:file|create|open|submit)\b.{0,20}\bticket\b"
    r"|\bsupport ticket\b",
    re.IGNORECASE,
)
TICKET_PHRASE_RE = re.compile(
    r"(?:please\s+)?(?:create|file|open|submit|raise|make)(?:\s+a|\s+me)?(?:\s+support)?\s+ticket[,\s:]*"
    r"|(?:i want to|i'd like to|i would like to)\s+(?:file|create|open|submit)(?:\s+a)?(?:\s+support)?\s+ticket[,\s:]*"
    r"|support ticket[,\s:]*",
    re.IGNORECASE,
)
REFUSAL_RE = re.compile(
    r"\b("
    r"delete my account|delete all my (?:data|builds)|delete my (?:data|builds)|"
    r"cancel my subscription|cancel subscription|wipe my (?:account|data)|"
    r"remove my account|erase my (?:account|data)|close my account|"
    r"permanently delete|gdpr delete"
    r")\b",
    re.IGNORECASE,
)
QUESTION_RE = re.compile(
    r"^\s*(what|who|when|where|why|how|does|do|is|are|can|could|would|will)\b|[?]\s*$",
    re.IGNORECASE,
)
CLARIFICATION_MESSAGE = "What issue should I include in the support ticket?"
REFUSAL_MESSAGE = (
    "I can only create support tickets. I cannot delete accounts, "
    "cancel subscriptions, or change billing."
)


@dataclass
class RouteDecision:
    route: str
    summary: str | None = None
    priority: str | None = None
    message: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def _extract_summary(message: str) -> str:
    cleaned = TICKET_PHRASE_RE.sub(" ", message)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-")
    return cleaned


def _heuristic_route(message: str) -> RouteDecision:
    if REFUSAL_RE.search(message) and not QUESTION_RE.search(message):
        return RouteDecision(route="refusal", message=REFUSAL_MESSAGE)

    if TICKET_RE.search(message):
        summary = _extract_summary(message)
        if len(summary) < 12:
            return RouteDecision(route="clarification", message=CLARIFICATION_MESSAGE)
        return RouteDecision(
            route="tool_call",
            summary=summary,
            priority=infer_priority(message),
        )

    return RouteDecision(route="rag")


def _with_usage(decision: RouteDecision, usage: LLMResult) -> RouteDecision:
    decision.prompt_tokens = usage.prompt_tokens
    decision.completion_tokens = usage.completion_tokens
    decision.total_tokens = usage.total_tokens
    return decision


def _llm_route(message: str, provider: LLMProvider) -> RouteDecision | None:
    result = provider.generate(
        AGENT_SYSTEM_PROMPT,
        f"User message:\n{message}\n\nReturn the routing JSON only.",
        temperature=0.0,
    )
    raw = result.text
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(raw[start : end + 1])
    except (json.JSONDecodeError, TypeError):
        return None

    route = data.get("route")
    decision: RouteDecision | None = None
    if route == "rag":
        decision = RouteDecision(route="rag")
    elif route == "tool_call":
        summary = (data.get("summary") or "").strip()
        if len(summary) < 12:
            decision = RouteDecision(route="clarification", message=CLARIFICATION_MESSAGE)
        else:
            decision = RouteDecision(
                route="tool_call",
                summary=summary,
                priority=data.get("priority") or infer_priority(message),
            )
    elif route == "clarification":
        decision = RouteDecision(
            route="clarification",
            message=data.get("message") or CLARIFICATION_MESSAGE,
        )
    elif route == "refusal":
        decision = RouteDecision(route="refusal", message=data.get("message") or REFUSAL_MESSAGE)
    if decision is None:
        return None
    return _with_usage(decision, result)


def route_message(message: str, provider: LLMProvider) -> RouteDecision:
    """Deterministic routing first; LLM only used as a tie-break when unused.

    Guardrails (missing summary, out-of-scope actions) stay heuristic so they
    remain explainable and work without an API key.
    """
    decision = _heuristic_route(message)
    if decision.route in {"tool_call", "clarification", "refusal"}:
        return decision
    if isinstance(provider, StubProvider):
        return decision
    llm_decision = _llm_route(message, provider)
    if llm_decision and llm_decision.route in {"rag", "refusal", "tool_call", "clarification"}:
        if llm_decision.route == "tool_call" and not llm_decision.summary:
            return RouteDecision(route="clarification", message=CLARIFICATION_MESSAGE)
        return llm_decision
    return decision
