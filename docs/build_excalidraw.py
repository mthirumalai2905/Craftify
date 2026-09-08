"""Generate a single Excalidraw system-design scene for Craftify."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).with_name("craftify-system-design.excalidraw")

N = {"n": 1}


def nid(prefix: str) -> str:
    N["n"] += 1
    return f"{prefix}{N['n']}"


def base(**extra):
    el = {
        "id": extra.pop("id"),
        "x": extra.pop("x"),
        "y": extra.pop("y"),
        "angle": 0,
        "strokeColor": extra.pop("strokeColor", "#3f3f46"),
        "backgroundColor": extra.pop("backgroundColor", "#ffffff"),
        "fillStyle": "solid",
        "strokeWidth": extra.pop("strokeWidth", 1.5),
        "strokeStyle": extra.pop("strokeStyle", "solid"),
        "roughness": 0,
        "opacity": 100,
        "groupIds": extra.pop("groupIds", []),
        "frameId": None,
        "roundness": extra.pop("roundness", {"type": 3}),
        "seed": N["n"],
        "version": 1,
        "versionNonce": N["n"] * 17,
        "isDeleted": False,
        "boundElements": extra.pop("boundElements", None),
        "updated": 1,
        "link": None,
        "locked": False,
        "index": extra.pop("index", None),
    }
    el.update(extra)
    return {k: v for k, v in el.items() if v is not None}


def rect(x, y, w, h, fill="#ffffff", stroke="#3f3f46", sw=1.5, dashed=False):
    return base(
        id=nid("r"),
        type="rectangle",
        x=x,
        y=y,
        width=w,
        height=h,
        backgroundColor=fill,
        strokeColor=stroke,
        strokeWidth=sw,
        strokeStyle="dashed" if dashed else "solid",
        roundness={"type": 3},
    )


def diamond(x, y, w, h, fill="#fafafa", stroke="#3f3f46"):
    return base(
        id=nid("d"),
        type="diamond",
        x=x,
        y=y,
        width=w,
        height=h,
        backgroundColor=fill,
        strokeColor=stroke,
        roundness=None,
    )


def text(x, y, s, size=14, color="#18181b", align="left", w=None, family=2, bold=False):
    width = w if w is not None else max(40, int(len(s) * size * 0.52))
    height = int(size * 1.45) * (s.count("\n") + 1)
    return base(
        id=nid("t"),
        type="text",
        x=x,
        y=y,
        width=width,
        height=height,
        text=s,
        originalText=s,
        fontSize=size,
        fontFamily=3 if family == 3 else 2,
        textAlign=align,
        verticalAlign="top",
        baseline=int(size * 1.15),
        strokeColor=color,
        backgroundColor="transparent",
        roundness=None,
        containerId=None,
        autoResize=True,
        lineHeight=1.25,
    )


def arrow(x1, y1, x2, y2, color="#52525b", label=None):
    els = []
    aid = nid("a")
    els.append(
        base(
            id=aid,
            type="arrow",
            x=x1,
            y=y1,
            width=abs(x2 - x1) or 1,
            height=abs(y2 - y1) or 1,
            strokeColor=color,
            backgroundColor="transparent",
            strokeWidth=1.5,
            roundness={"type": 2},
            points=[[0, 0], [x2 - x1, y2 - y1]],
            lastCommittedPoint=None,
            startBinding=None,
            endBinding=None,
            startArrowhead=None,
            endArrowhead="arrow",
            elbowed=False,
        )
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        els.append(text(mx - 40, my - 18, label, size=11, color="#71717a", w=120, align="center"))
    return els


def labeled_box(x, y, w, h, title, body, fill, stroke, title_size=14):
    els = [rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5)]
    els.append(text(x + 14, y + 12, title, size=title_size, color=stroke, w=w - 28))
    if body:
        els.append(text(x + 14, y + 36, body, size=12, color="#3f3f46", w=w - 28, family=3))
    return els


elements = []

# Canvas title
elements += [
    text(60, 36, "Craftify Support — System Design", size=28, color="#18181b", w=720),
    text(
        60,
        78,
        "Request path: Next.js chat → FastAPI /ask → agent router → RAG | tool | clarification | refusal",
        size=14,
        color="#71717a",
        w=1100,
    ),
]

# ===== 1. Client =====
elements += [rect(40, 130, 280, 520, fill="#fafafa", stroke="#d4d4d8", sw=1)]
elements.append(text(56, 144, "1  CLIENT", size=12, color="#71717a", w=200))
elements += labeled_box(
    60,
    176,
    240,
    88,
    "User / Browser",
    "Asks a Craftify question\nor files a support ticket",
    "#ffffff",
    "#3f3f46",
)
elements += arrow(180, 264, 180, 300)
elements += labeled_box(
    60,
    300,
    240,
    200,
    "Next.js chat  :3001",
    "app/page.tsx\nPOST /ask\n5 response cards\nloading / error / empty",
    "#eef2ff",
    "#4f46e5",
)
elements += labeled_box(
    60,
    516,
    240,
    116,
    "Render by type",
    "answer + sources\nabstention  NOT IN DOCS\ntool_call   TKT-id\nclarify / refuse",
    "#ffffff",
    "#4f46e5",
)

# ===== 2. API =====
elements += [rect(360, 130, 280, 520, fill="#fafafa", stroke="#d4d4d8", sw=1)]
elements.append(text(376, 144, "2  API", size=12, color="#71717a", w=200))
elements += arrow(300, 360, 380, 360, label="JSON")
elements += labeled_box(
    380,
    176,
    240,
    120,
    "FastAPI  :8000",
    "app/main.py\nPOST /ask\nGET  /health\nCORS localhost",
    "#eef2ff",
    "#4338ca",
)
elements += labeled_box(
    380,
    316,
    240,
    140,
    "LLM provider",
    "app/llm/provider.py\ngenerate(sys, user)\nDeepSeek  if key set\nstub       if key missing",
    "#ecfdf5",
    "#047857",
)
elements += labeled_box(
    380,
    476,
    240,
    140,
    "Prompts (files)",
    "prompts/rag_prompt.py\n  corpus-only, abstain\nprompts/agent_prompt.py\n  4-route few-shots",
    "#fff7ed",
    "#c2410c",
)

# ===== 3. Router =====
elements += [rect(680, 130, 300, 520, fill="#fafafa", stroke="#d4d4d8", sw=1)]
elements.append(text(696, 144, "3  AGENT ROUTER", size=12, color="#71717a", w=240))
elements += arrow(620, 230, 700, 230)
elements += labeled_box(
    700,
    176,
    260,
    150,
    "router.py  (heuristic)",
    "ticket + summary  → tool\nticket, no issue   → clarify\ndelete / cancel    → refuse\nelse               → RAG\nquestions about\ndelete stay on RAG",
    "#f5f3ff",
    "#6d28d9",
)
elements += labeled_box(700, 346, 260, 64, "tool_call", "create_support_ticket", "#eff6ff", "#1d4ed8")
elements += labeled_box(700, 422, 260, 64, "RAG", "retrieve + DeepSeek", "#ecfdf5", "#047857")
elements += labeled_box(700, 498, 124, 64, "clarify", "need summary", "#f5f3ff", "#6d28d9")
elements += labeled_box(836, 498, 124, 64, "refuse", "out of scope", "#fef2f2", "#b91c1c")

# ===== 4. RAG =====
elements += [rect(1020, 130, 560, 360, fill="#f0fdf4", stroke="#86efac", sw=1)]
elements.append(text(1036, 144, "4  RAG  — Chroma Cloud hybrid search", size=12, color="#047857", w=420))
elements += arrow(960, 454, 1040, 280)
elements += labeled_box(
    1040,
    176,
    250,
    130,
    "retrieve.py",
    "embed question\ntop-K  (RAG_TOP_K=4)\nGroupBy document_id",
    "#ffffff",
    "#047857",
)
elements += labeled_box(
    1310,
    176,
    250,
    130,
    "store.py",
    "CloudClient\nget_or_create + Schema\nin-memory fallback",
    "#ffffff",
    "#047857",
)
elements += labeled_box(
    1040,
    322,
    250,
    148,
    "craftify_docs",
    "Build Documentation\n13 files  doc_01–13",
    "#ffffff",
    "#0f766e",
)
elements += labeled_box(
    1310,
    322,
    250,
    148,
    "craftify_tickets",
    "Support Tickets\n7 files  ticket_101–107",
    "#ffffff",
    "#0f766e",
)

# Embeddings strip
elements += labeled_box(
    1020,
    510,
    270,
    140,
    "Dense  Qwen",
    "Chroma Cloud Qwen\n0.6B  task=retrieval",
    "#ecfeff",
    "#0e7490",
)
elements += labeled_box(
    1310,
    510,
    270,
    140,
    "Sparse  Splade + RRF",
    "weights 0.7 / 0.3\nReciprocal Rank Fusion",
    "#ecfeff",
    "#0e7490",
)

# DeepSeek + grounding
elements += labeled_box(
    1600,
    176,
    260,
    200,
    "DeepSeek  chat",
    "system = RAG prompt\nuser   = chunks + Q\nJSON answer | abstain\nnever general Minecraft",
    "#ecfdf5",
    "#047857",
)
elements += arrow(1570, 240, 1600, 240)
elements += labeled_box(
    1600,
    396,
    260,
    120,
    "Grounded response",
    "type: answer | abstention\nsources: file + snippet",
    "#ffffff",
    "#047857",
)

# ===== 5. Tool =====
elements += [rect(1020, 680, 560, 220, fill="#eff6ff", stroke="#93c5fd", sw=1)]
elements.append(text(1036, 694, "5  TOOL", size=12, color="#1d4ed8", w=200))
elements += arrow(830, 378, 1020, 760, color="#1d4ed8")
elements += labeled_box(
    1040,
    724,
    250,
    150,
    "create_support_ticket",
    "mock  tools.py\nsummary  required\npriority  keyword heuristic\nreturns TKT-####",
    "#ffffff",
    "#1d4ed8",
)
elements += labeled_box(
    1310,
    724,
    250,
    150,
    "logs/tool_calls.jsonl",
    "timestamp\ntool name\ninputs  summary/priority\noutputs ticket_id/status",
    "#ffffff",
    "#1d4ed8",
)
elements += arrow(1290, 800, 1310, 800, color="#1d4ed8")

# ===== 6. Ingestion =====
elements += [rect(40, 680, 940, 220, fill="#fffbeb", stroke="#fcd34d", sw=1)]
elements.append(text(56, 694, "6  INGESTION  (startup + migrate script)", size=12, color="#b45309", w=420))
elements += labeled_box(
    60,
    724,
    210,
    150,
    "Corpus  20 .txt",
    "Title: / Category:\nbackend/data/corpus\ntaskCorpus  source",
    "#ffffff",
    "#b45309",
)
elements += labeled_box(
    290,
    724,
    220,
    150,
    "ingest.py",
    "strip header → metadata\n1 chunk if ≤1500 chars\nelse paragraph / lines\nkeep Category",
    "#ffffff",
    "#b45309",
)
elements += labeled_box(
    530,
    724,
    210,
    150,
    "migrate_to_chroma_cloud.py",
    "upsert both collections\nre-runnable  get_or_create",
    "#ffffff",
    "#b45309",
)
elements += labeled_box(
    760,
    724,
    200,
    150,
    "Shard by category",
    "docs  ≠  tickets\nmutually exclusive",
    "#ffffff",
    "#b45309",
)
elements += arrow(270, 800, 290, 800, color="#b45309")
elements += arrow(510, 800, 530, 800, color="#b45309")
elements += arrow(740, 800, 760, 800, color="#b45309")

# ===== 7. Eval =====
elements += [rect(1600, 540, 260, 360, fill="#f8fafc", stroke="#cbd5e1", sw=1)]
elements.append(text(1616, 554, "7  EVALUATION", size=12, color="#475569", w=200))
elements += labeled_box(
    1620,
    584,
    220,
    140,
    "questions.json",
    "15 golden questions\nA RAG  B abstain\nC tool  D clarify\nE refuse",
    "#ffffff",
    "#475569",
)
elements += labeled_box(
    1620,
    740,
    220,
    140,
    "evaluate.py",
    "hits live /ask\n15/15  100%\ncategory rubric",
    "#ffffff",
    "#475569",
)

# ===== 8. Minecraft (standalone) =====
elements += [rect(40, 930, 1820, 200, fill="#fafafa", stroke="#a1a1aa", sw=1, dashed=True)]
elements.append(
    text(
        56,
        944,
        "8  MINECRAFT ASSETS  — standalone, not connected to RAG / corpus / /ask",
        size=12,
        color="#71717a",
        w=800,
    )
)
elements += labeled_box(
    60,
    980,
    280,
    128,
    "Magic Crystal",
    "texture/  16×16 PNG\nmodel/    2 cuboids\nscreenshots/",
    "#ffffff",
    "#3f3f46",
)
elements += labeled_box(
    360,
    980,
    520,
    128,
    "Ores  (stone + patches)",
    "coal  black     iron  orange-brown\ndiamond  cyan   gold  yellow\nemerald  green   cube_all models",
    "#ffffff",
    "#3f3f46",
)
elements += labeled_box(
    900,
    980,
    420,
    128,
    "Generator scripts",
    "scripts/make_minecraft_asset.py\nscripts/make_minecraft_ores.py",
    "#ffffff",
    "#3f3f46",
)
elements += labeled_box(
    1340,
    980,
    500,
    128,
    "Why isolated",
    "Corpus is Craftify product docs.\nPart 4 must not reference RAG.",
    "#ffffff",
    "#3f3f46",
)

# Legend
elements.append(
    text(
        60,
        1156,
        "Keys stay in backend/.env (never logged).  No auth / no DB / no agent framework.  Interview story: one process, four routes, hybrid retrieval, mock ticket + JSONL audit.",
        size=13,
        color="#71717a",
        w=1700,
    )
)

scene = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {
        "gridSize": 20,
        "gridStep": 5,
        "gridModeEnabled": False,
        "viewBackgroundColor": "#ffffff",
    },
    "files": {},
}

OUT.write_text(json.dumps(scene, indent=2), encoding="utf-8")
print(f"Wrote {OUT}  elements={len(elements)}")
