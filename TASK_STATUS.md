# Craftify Assessment — Task Status

Running checklist. Updated as work lands, not only at the end.

## Part 1 — RAG

- [x] Inspected corpus (20 plain-text files, `Title:` / `Category:` headers)
- [x] Document ingestion + chunking
- [x] Chroma Cloud hybrid store (Qwen dense + Splade sparse + RRF + GroupBy)
- [x] Local in-memory fallback when Chroma Cloud creds are missing
- [x] `/ask` RAG path
- [x] Abstention when evidence is insufficient

## Part 2 — Agent / Tool / Guardrail / Logging

- [x] `create_support_ticket` mock
- [x] Guardrail: summary required, priority heuristic
- [x] Router: RAG / tool / clarification / refusal
- [x] JSONL tool-call logging

## Part 3 — Frontend

- [x] Next.js chat skeleton
- [x] Connected to `POST /ask`
- [x] Five response types rendered per design system
- [x] Loading, disabled send, API error, empty state

## Part 4 — Minecraft asset

- [x] 16x16 PNG texture
- [x] Java model JSON
- [x] Screenshot
- [x] `minecraft/README.md` workflow note

## Part 5 — Evaluation + write-up

- [x] Golden set (15 questions, 5 categories)
- [x] `evaluate.py` run against live backend
- [x] Real results captured in README (15/15, 100.0%)
- [x] README: architecture, eval, weakness, trade-offs, prompts, Minecraft

## Engineering hygiene

- [x] `.gitignore` excludes secrets and caches
- [x] `backend/.env.example` present, no secrets committed
- [x] App boots without `DEEPSEEK_API_KEY` (stub provider)
- [x] Fresh-clone install path documented in README
