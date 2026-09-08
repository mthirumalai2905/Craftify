"""Copy the local Craftify corpus into Chroma Cloud collections.

Re-runnable: uses upsert and get_or_create. Shards Build Documentation and
Support Tickets into separate collections, embeds with Chroma Cloud Qwen
(dense) + Splade (sparse).
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings  # noqa: E402
from app.rag.ingest import load_corpus  # noqa: E402
from app.rag.store import VectorStore  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.chroma_cloud_configured:
        raise SystemExit(
            "Chroma Cloud env vars are missing. Set CHROMA_API_KEY, "
            "CHROMA_TENANT, and CHROMA_DATABASE in backend/.env"
        )
    chunks = load_corpus(settings.corpus_path)
    store = VectorStore(settings)
    count = store.upsert(chunks)
    print(f"Upserted {count} chunks into Chroma Cloud")
    print(f"  docs collection:    {settings.chroma_collection_docs}")
    print(f"  tickets collection: {settings.chroma_collection_tickets}")
    print(f"  store.count():      {store.count()}")


if __name__ == "__main__":
    main()
