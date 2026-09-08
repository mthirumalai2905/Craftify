from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb import (
    K,
    Knn,
    Rrf,
    Schema,
    Search,
    SparseVectorIndexConfig,
    VectorIndexConfig,
)
from chromadb.execution.expression.operator import GroupBy, MinK
from chromadb.utils.embedding_functions.chroma_cloud_qwen_embedding_function import (
    ChromaCloudQwenEmbeddingFunction,
    ChromaCloudQwenEmbeddingModel,
    ChromaCloudQwenEmbeddingTarget,
)
from chromadb.utils.embedding_functions.chroma_cloud_splade_embedding_function import (
    ChromaCloudSpladeEmbeddingFunction,
    ChromaCloudSpladeEmbeddingModel,
)

from app.config import Settings
from app.rag.ingest import Chunk

logger = logging.getLogger("craftify.rag")

DOCS_CATEGORY = "Build Documentation"
TICKETS_CATEGORY = "Support Ticket"


@dataclass
class RetrievedChunk:
    document_name: str
    document_id: str
    chunk_id: str
    source_path: str
    category: str
    title: str
    text: str
    score: float | None
    snippet: str


def _snippet(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _qwen_fn() -> ChromaCloudQwenEmbeddingFunction:
    return ChromaCloudQwenEmbeddingFunction(
        model=ChromaCloudQwenEmbeddingModel.QWEN3_EMBEDDING_0p6B,
        task="retrieval",
        instructions={
            "retrieval": {
                ChromaCloudQwenEmbeddingTarget.DOCUMENTS: (
                    "Represent this Craftify product-support document for retrieval."
                ),
                ChromaCloudQwenEmbeddingTarget.QUERY: (
                    "Represent this Craftify support question for retrieving the matching document."
                ),
            }
        },
    )


def _splade_fn() -> ChromaCloudSpladeEmbeddingFunction:
    return ChromaCloudSpladeEmbeddingFunction(
        model=ChromaCloudSpladeEmbeddingModel.SPLADE_PP_EN_V1
    )


def _hybrid_schema() -> Schema:
    schema = Schema()
    schema.create_index(
        config=VectorIndexConfig(
            space="cosine",
            embedding_function=_qwen_fn(),
        )
    )
    schema.create_index(
        config=SparseVectorIndexConfig(
            source_key=K.DOCUMENT,
            embedding_function=_splade_fn(),
        ),
        key="sparse_embedding",
    )
    return schema


def _hybrid_search(query: str, k: int) -> Search:
    candidate_limit = max(20, k * 8)
    hybrid = Rrf(
        ranks=[
            Knn(query=query, return_rank=True, limit=candidate_limit, default=1000),
            Knn(
                query=query,
                key="sparse_embedding",
                return_rank=True,
                limit=candidate_limit,
                default=1000,
            ),
        ],
        weights=[0.7, 0.3],
        k=60,
        normalize=True,
    )
    return (
        Search()
        .rank(hybrid)
        .group_by(GroupBy(keys=K("document_id"), aggregate=MinK(keys=K.SCORE, k=1)))
        .limit(k)
        .select(K.DOCUMENT, K.SCORE, K.METADATA, K.ID)
    )


def _rows_to_chunks(rows: list[dict[str, Any]]) -> list[RetrievedChunk]:
    results: list[RetrievedChunk] = []
    for row in rows:
        metadata = row.get("metadata") or {}
        text = row.get("document") or ""
        results.append(
            RetrievedChunk(
                document_name=metadata.get("document_name", ""),
                document_id=metadata.get("document_id", ""),
                chunk_id=metadata.get("chunk_id", row.get("id", "")),
                source_path=metadata.get("source_path", ""),
                category=metadata.get("category", ""),
                title=metadata.get("title", ""),
                text=text,
                score=row.get("score"),
                snippet=_snippet(text),
            )
        )
    return results


class VectorStore:
    """Chroma Cloud hybrid store, with an in-memory fallback when creds are missing."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cloud = settings.chroma_cloud_configured
        if self.cloud:
            self._init_cloud()
        else:
            logger.warning(
                "Chroma Cloud credentials are unset — using in-memory Chroma fallback"
            )
            self._init_local()

    def _init_cloud(self) -> None:
        import os

        os.environ["CHROMA_API_KEY"] = self.settings.chroma_api_key
        kwargs: dict[str, Any] = {
            "tenant": self.settings.chroma_tenant,
            "database": self.settings.chroma_database,
            "api_key": self.settings.chroma_api_key,
        }
        if self.settings.chroma_host and self.settings.chroma_host != "api.trychroma.com":
            kwargs["cloud_host"] = self.settings.chroma_host
        self.client = chromadb.CloudClient(**kwargs)
        schema = _hybrid_schema()
        self.docs = self.client.get_or_create_collection(
            name=self.settings.chroma_collection_docs,
            schema=schema,
        )
        self.tickets = self.client.get_or_create_collection(
            name=self.settings.chroma_collection_tickets,
            schema=schema,
        )
        self.local = None
        logger.info(
            "Chroma Cloud ready (docs=%s, tickets=%s)",
            self.settings.chroma_collection_docs,
            self.settings.chroma_collection_tickets,
        )

    def _init_local(self) -> None:
        self.client = chromadb.Client()
        self.local = self.client.get_or_create_collection(name="craftify_local")
        self.docs = None
        self.tickets = None

    def _collection_for(self, category: str):
        if category == TICKETS_CATEGORY:
            return self.tickets
        return self.docs

    def upsert(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        if self.cloud:
            by_category: dict[str, list[Chunk]] = {DOCS_CATEGORY: [], TICKETS_CATEGORY: []}
            for chunk in chunks:
                bucket = (
                    TICKETS_CATEGORY
                    if chunk.category == TICKETS_CATEGORY
                    else DOCS_CATEGORY
                )
                by_category[bucket].append(chunk)
            count = 0
            for category, group in by_category.items():
                if not group:
                    continue
                collection = self._collection_for(category)
                collection.upsert(
                    ids=[c.id for c in group],
                    documents=[c.text for c in group],
                    metadatas=[c.metadata() for c in group],
                )
                count += len(group)
            return count

        assert self.local is not None
        self.local.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[c.metadata() for c in chunks],
        )
        return len(chunks)

    def count(self) -> int:
        if self.cloud:
            return int(self.docs.count()) + int(self.tickets.count())
        assert self.local is not None
        return int(self.local.count())

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        if self.cloud:
            return self._search_cloud(query, k)
        return self._search_local(query, k)

    def _search_cloud(self, query: str, k: int) -> list[RetrievedChunk]:
        per_collection = max(k, 2)
        search = _hybrid_search(query, per_collection)
        merged: list[RetrievedChunk] = []
        for collection in (self.docs, self.tickets):
            try:
                result = collection.search(search)
                rows = result.rows()[0] if result.rows() else []
                merged.extend(_rows_to_chunks(rows))
            except Exception as exc:
                logger.warning("Cloud hybrid search failed on %s: %s", collection.name, exc)
        merged.sort(key=lambda item: (item.score is None, item.score if item.score is not None else 0.0))
        seen: set[str] = set()
        unique: list[RetrievedChunk] = []
        for item in merged:
            key = item.document_id or item.chunk_id
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
            if len(unique) >= k:
                break
        return unique

    def _search_local(self, query: str, k: int) -> list[RetrievedChunk]:
        assert self.local is not None
        n = min(k, max(self.local.count(), 1))
        raw = self.local.query(query_texts=[query], n_results=n)
        ids = (raw.get("ids") or [[]])[0]
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        results: list[RetrievedChunk] = []
        for index, chunk_id in enumerate(ids):
            metadata = metas[index] or {}
            text = docs[index] or ""
            distance = distances[index] if index < len(distances) else None
            results.append(
                RetrievedChunk(
                    document_name=metadata.get("document_name", ""),
                    document_id=metadata.get("document_id", ""),
                    chunk_id=metadata.get("chunk_id", chunk_id),
                    source_path=metadata.get("source_path", ""),
                    category=metadata.get("category", ""),
                    title=metadata.get("title", ""),
                    text=text,
                    score=distance,
                    snippet=_snippet(text),
                )
            )
        return results
