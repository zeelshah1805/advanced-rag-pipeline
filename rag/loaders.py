"""Document loaders + chunking.

Loaders return a list of (text, page) segments per document so we can keep a
real `page` on every chunk — PDFs are loaded page-by-page, plain text as one
segment. Chunking is recursive (~500 tokens, ~80 overlap) and records exact
char offsets, which is what makes citations point back to a precise span.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CONFIG
from .schema import Chunk

SUPPORTED = {".pdf", ".txt", ".md"}

# ~4 chars per token heuristic, so chunk_size/overlap (in "tokens") map to chars
_CHARS_PER_TOKEN = 4


def discover(paths: Iterable[Path]) -> list[Path]:
    """Expand a list of files/dirs into supported document files."""
    out: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out.extend(
                f for f in sorted(p.rglob("*")) if f.suffix.lower() in SUPPORTED
            )
        elif p.suffix.lower() in SUPPORTED:
            out.append(p)
    return out


def _load_segments(path: Path) -> list[tuple[str, int | None]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        segments: list[tuple[str, int | None]] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                segments.append((text, i + 1))  # 1-based page numbers
        return segments
    # .txt / .md
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(text, None)]


def _clean(text: str) -> str:
    # collapse runaway whitespace from PDF extraction without destroying offsets badly
    return re.sub(r"[ \t]+", " ", text).strip()


def chunk_document(path: Path) -> list[Chunk]:
    doc_id = path.stem
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CONFIG.chunk_size * _CHARS_PER_TOKEN,
        chunk_overlap=CONFIG.chunk_overlap * _CHARS_PER_TOKEN,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=True,
    )
    chunks: list[Chunk] = []
    idx = 0
    for seg_text, page in _load_segments(path):
        seg_text = _clean(seg_text)
        if not seg_text:
            continue
        cursor = 0
        for piece in splitter.split_text(seg_text):
            piece = piece.strip()
            if not piece:
                continue
            start = seg_text.find(piece, cursor)
            if start == -1:
                start = cursor
            end = start + len(piece)
            cursor = max(cursor, end - CONFIG.chunk_overlap * _CHARS_PER_TOKEN)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}::c{idx:05d}",
                    doc_id=doc_id,
                    source=path.name,
                    page=page,
                    char_start=start,
                    char_end=end,
                    text=piece,
                )
            )
            idx += 1
    return chunks


def load_corpus(paths: Iterable[Path]) -> list[Chunk]:
    files = discover(paths)
    if not files:
        raise FileNotFoundError(
            f"No supported documents ({', '.join(sorted(SUPPORTED))}) found in: "
            f"{[str(p) for p in paths]}"
        )
    all_chunks: list[Chunk] = []
    for f in files:
        all_chunks.extend(chunk_document(f))
    return all_chunks
