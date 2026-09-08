from __future__ import annotations

from app.config import Settings
from app.rag.ingest import load_corpus
from app.rag.store import RetrievedChunk, VectorStore

_store: VectorStore | None = None


def get_store(settings: Settings) -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(settings)
        if _store.count() == 0:
            chunks = load_corpus(settings.corpus_path)
            _store.upsert(chunks)
    return _store


def retrieve(question: str, settings: Settings) -> list[RetrievedChunk]:
    store = get_store(settings)
    return store.search(question, settings.rag_top_k)


def format_context(chunks: list[RetrievedChunk]) -> list[str]:
    blocks: list[str] = []
    for chunk in chunks:
        blocks.append(
            f"Document: {chunk.document_name}\n"
            f"Title: {chunk.title}\n"
            f"Category: {chunk.category}\n"
            f"Content:\n{chunk.text}"
        )
    return blocks
