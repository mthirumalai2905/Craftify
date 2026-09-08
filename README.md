# Craftify Support Assessment

Small RAG + tool-calling support app over the Craftify corpus. The Minecraft asset is a separate deliverable and does not use the corpus.

## Architecture

**Frontend.** Next.js (App Router) chat page. `POST /ask` responses render as answer, abstention, tool call, clarification, or refusal.

**Backend.** FastAPI. One endpoint, `/ask`, plus `/health`.

**Agent.** Deterministic router in `backend/app/agent/router.py`. Ticket language with a summary → tool; ticket language without a summary → clarification; destructive account/billing commands → refusal; questions → RAG. An optional DeepSeek routing pass exists but guardrails stay heuristic so they work without a key.

**RAG.** Corpus files are parsed as `Title:` / `Category:` plain text, then chunked (one chunk per short file; paragraph/line split only above ~1500 characters). Chunks are upserted into **Chroma Cloud**, sharded by category:

- `craftify_docs` — Build Documentation
- `craftify_tickets` — Support Tickets

Each collection uses a Schema with **Chroma Cloud Qwen** dense embeddings and **Chroma Cloud Splade** sparse embeddings. Retrieval is hybrid **RRF**, then **GroupBy `document_id`** so one document does not flood the context. If Cloud credentials are missing, the same wrapper falls back to in-memory Chroma.

**LLM.** `backend/app/llm/provider.py` exposes `generate(system, user) -> str`. DeepSeek when `DEEPSEEK_API_KEY` is set; otherwise a stub. No code change is required to switch — restart after editing `.env`.

**Tool.** `create_support_ticket(summary, priority)` is a mock. Every call appends one JSON line to `logs/tool_calls.jsonl`.

## Run

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
copy .env.example .env   # then add keys
.venv\Scripts\python.exe scripts\migrate_to_chroma_cloud.py
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

`backend/.env.example` lists every variable. The app boots without `DEEPSEEK_API_KEY` (stub answers) and without Chroma Cloud credentials (in-memory store). Re-ingest Cloud with `python scripts/migrate_to_chroma_cloud.py`.

### Docker (one command)

```bash
# copy backend/.env.example → backend/.env first if you have not already
docker compose up --build
```

Chroma Cloud / DeepSeek creds still come from `backend/.env`, same as the manual path. UI is at http://localhost:3000, API at http://localhost:8000. Tool-call lines persist in `logs/tool_calls.jsonl` on the host.

## Evaluation

`evaluation/questions.json` has 15 questions across five categories: answerable RAG (including ticket 1103 / `ticket_106`, the only escalated bug), unsupported abstention, tool call, clarification, and refusal.

`evaluation/evaluate.py` hits the live backend. Category-specific rubric: RAG correctness 0–3, grounding 0–2, completeness 0–2; agent routing 0–2 and tool arguments 0–1; guardrails 0–2.

**Latest run** (2026-09-08, DeepSeek + Chroma Cloud hybrid search):

```
A_answerable_rag: 6/6 passed
B_unsupported:    3/3 passed
C_tool_call:      2/2 passed
D_guardrail:      2/2 passed
E_refusal:        2/2 passed
Total: 15   Passed: 15   Failed: 0   Accuracy: 100.0%
```

“Good enough to ship” here means: corpus-backed questions return a grounded answer with the right source; out-of-corpus questions abstain; ticket intents route to tool / clarification / refusal correctly; the frontend can render each type.

## Biggest weakness

Retrieval is a single hybrid top-K pass with no reranker. A support ticket and the doc it cites are in different collections; if one ranks just outside K, the model never sees both. That showed up as a design risk more than an eval failure, because the golden questions are short and the corpus is tiny.

## Trade-offs

- One chunk per short document instead of overlapping windows. The 20 files are 400–700 words; extra chunking would mostly duplicate embeddings.
- Guardrails are keyword/heuristic, not an LLM call. Easier to defend in an interview and they work with the stub provider. The cost is brittle phrasing (a question about “delete my account” must not be treated as a delete command).
- Hybrid RRF + GroupBy were added for Chroma Cloud. Local fallback uses dense `query()` only.
- No auth, no database, no agent framework.

## System prompts

- RAG: [`backend/app/prompts/rag_prompt.py`](backend/app/prompts/rag_prompt.py) — use only retrieved chunks; never use general Minecraft/AI knowledge; abstain when evidence is thin.
- Agent: [`backend/app/prompts/agent_prompt.py`](backend/app/prompts/agent_prompt.py) — one tool, routing table, clarification and refusal rules.

## Minecraft asset

Standalone voxel assets (not from the RAG corpus): the original Magic Crystal Block plus five stone-base ores (coal, iron, diamond, gold, emerald). Each has a 16×16 PNG, a Java cube model, and an isometric preview; the ores are also on one lineup shot in `minecraft/screenshots/ore_lineup.png`. See [`minecraft/README.md`](minecraft/README.md).
