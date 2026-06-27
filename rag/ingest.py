"""Ingestion entry point: load -> chunk -> embed -> build indexes.

One-time, offline. Run via `python -m scripts.ingest [paths...]`.
"""
from __future__ import annotations

from pathlib import Path

from .config import CONFIG
from .embeddings import get_embedder
from .loaders import load_corpus
from .stores import build_indexes


def ingest(paths: list[Path] | None = None) -> dict:
    """Build all three indexes from the given files/dirs. Defaults to the
    corpus dir, falling back to the bundled sample so a fresh clone runs."""
    if not paths:
        if _has_docs(_corpus_dir()):
            paths = [_corpus_dir()]
        else:
            print(f"[ingest] corpus empty — using bundled sample at {_sample_dir()}")
            paths = [_sample_dir()]

    print(f"[ingest] loading + chunking from: {[str(p) for p in paths]}")
    chunks = load_corpus(paths)
    print(f"[ingest] {len(chunks)} chunks; embedding with {CONFIG.embedding_model} ...")

    embedder = get_embedder()
    vectors = embedder.embed_passages([c.text for c in chunks])

    print("[ingest] building FAISS + BM25 + SQLite indexes ...")
    build_indexes(chunks, vectors)

    docs = sorted({c.doc_id for c in chunks})
    print(f"[ingest] done: {len(chunks)} chunks across {len(docs)} docs.")
    return {"chunks": len(chunks), "docs": len(docs), "doc_ids": docs}


def _corpus_dir() -> Path:
    from .config import CORPUS_DIR

    return CORPUS_DIR


def _sample_dir() -> Path:
    from .config import SAMPLE_DIR

    return SAMPLE_DIR


def _has_docs(d: Path) -> bool:
    from .loaders import discover

    return bool(discover([d])) if d.exists() else False
