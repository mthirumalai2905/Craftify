from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent.router import route_message
from app.agent.tools import create_support_ticket
from app.config import Settings, get_settings
from app.llm.provider import LLMProvider, StubProvider, get_provider
from app.logging_utils import log_tool_call
from app.prompts.rag_prompt import RAG_SYSTEM_PROMPT, build_rag_user_prompt
from app.rag.retrieve import format_context, get_store, retrieve
from app.rag.store import RetrievedChunk

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("craftify")

ABSTAIN_MESSAGE = "I couldn't find enough information in the provided documentation to answer that."


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    message: str | None = None

    @property
    def text(self) -> str:
        return (self.message or self.question).strip()


def _sources_from(chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for chunk in chunks:
        name = chunk.document_name
        if name in seen:
            continue
        seen.add(name)
        sources.append({"document": name, "snippet": chunk.snippet})
    return sources


def _parse_llm_json(raw: str) -> dict[str, Any] | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def _answer_from_rag(
    question: str,
    chunks: list[RetrievedChunk],
    provider: LLMProvider,
) -> dict[str, Any]:
    if not chunks:
        return {"type": "abstention", "message": ABSTAIN_MESSAGE, "sources": []}

    if isinstance(provider, StubProvider):
        return {
            "type": "answer",
            "answer": chunks[0].text,
            "sources": _sources_from(chunks),
            "provider": provider.name,
        }

    user_prompt = build_rag_user_prompt(question, format_context(chunks))
    raw = provider.generate(RAG_SYSTEM_PROMPT, user_prompt, temperature=0.0)
    parsed = _parse_llm_json(raw)
    if not parsed or parsed.get("type") == "abstention":
        return {"type": "abstention", "message": ABSTAIN_MESSAGE, "sources": []}

    cited = parsed.get("cited_documents") or []
    cited_set = {name.lower() for name in cited}
    selected = [c for c in chunks if c.document_name.lower() in cited_set] or chunks
    return {
        "type": "answer",
        "answer": parsed.get("answer") or raw,
        "sources": _sources_from(selected),
    }


def handle_ask(text: str, settings: Settings, provider: LLMProvider) -> dict[str, Any]:
    decision = route_message(text, provider)

    if decision.route == "clarification":
        return {"type": "clarification", "message": decision.message}

    if decision.route == "refusal":
        return {"type": "refusal", "message": decision.message}

    if decision.route == "tool_call":
        arguments = {
            "summary": decision.summary,
            "priority": decision.priority or "medium",
        }
        result = create_support_ticket(**arguments)
        log_tool_call(
            settings.resolved_log_path,
            "create_support_ticket",
            arguments,
            result,
        )
        return {
            "type": "tool_call",
            "tool": "create_support_ticket",
            "arguments": arguments,
            "result": result,
        }

    chunks = retrieve(text, settings)
    return _answer_from_rag(text, chunks, provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.provider = get_provider(settings)
    try:
        store = get_store(settings)
        logger.info("Vector store ready with %s chunks", store.count())
    except Exception as exc:
        logger.warning("Vector store warmup failed: %s", exc)
    yield


app = FastAPI(title="Craftify Support", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    settings: Settings = app.state.settings
    provider: LLMProvider = app.state.provider
    return {
        "ok": True,
        "llm": provider.name,
        "chroma_cloud": settings.chroma_cloud_configured,
    }


@app.post("/ask")
def ask(payload: AskRequest) -> dict[str, Any]:
    text = payload.text
    if not text:
        raise HTTPException(status_code=400, detail="question is required")
    try:
        return handle_ask(text, app.state.settings, app.state.provider)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("ask failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
