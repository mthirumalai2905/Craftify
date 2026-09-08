from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

HEADER_RE = re.compile(r"^Title:\s*(.+)\s*\nCategory:\s*(.+)\s*\n\n?", re.MULTILINE)
MAX_SINGLE_CHUNK_CHARS = 1500
MAX_RECORD_CHARS = 12_000  # well under Chroma Cloud's 16 KiB document limit


@dataclass
class Chunk:
    id: str
    text: str
    document_name: str
    document_id: str
    chunk_id: str
    chunk_index: int
    source_path: str
    category: str
    title: str

    def metadata(self) -> dict:
        return {
            "document_name": self.document_name,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "source_path": self.source_path,
            "category": self.category,
            "title": self.title,
        }

    def as_dict(self) -> dict:
        return asdict(self)


def parse_document(path: Path) -> tuple[str, str, str]:
    raw = path.read_text(encoding="utf-8")
    match = HEADER_RE.match(raw)
    if not match:
        raise ValueError(f"{path.name} is missing the Title:/Category: header")
    title = match.group(1).strip()
    category = match.group(2).strip()
    body = raw[match.end() :].strip()
    return title, category, body


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts or [text]


def _split_lines(text: str, max_chars: int) -> list[str]:
    lines = text.splitlines() or [text]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        addition = len(line) + 1
        if current and current_len + addition > max_chars:
            chunks.append("\n".join(current).strip())
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += addition
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def chunk_body(body: str) -> list[str]:
    """One chunk per short document; paragraph then line split if it grows."""
    if len(body) <= MAX_SINGLE_CHUNK_CHARS:
        return [body]
    chunks: list[str] = []
    for paragraph in _split_paragraphs(body):
        if len(paragraph) <= MAX_SINGLE_CHUNK_CHARS:
            chunks.append(paragraph)
        else:
            chunks.extend(_split_lines(paragraph, MAX_SINGLE_CHUNK_CHARS))
    return chunks or [body[:MAX_SINGLE_CHUNK_CHARS]]


def load_corpus(corpus_dir: Path) -> list[Chunk]:
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.txt")):
        title, category, body = parse_document(path)
        document_id = path.stem
        parts = chunk_body(body)
        for index, text in enumerate(parts):
            if len(text) > MAX_RECORD_CHARS:
                text = text[:MAX_RECORD_CHARS]
            chunk_id = f"{document_id}::chunk-{index:02d}"
            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=text,
                    document_name=path.name,
                    document_id=document_id,
                    chunk_id=chunk_id,
                    chunk_index=index,
                    source_path=str(path),
                    category=category,
                    title=title,
                )
            )
    return chunks
