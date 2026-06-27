"""Persistence layer: three coordinated stores written by ingestion and read by
retrieval.

- FAISS  (faiss.index)  — dense vectors, inner-product == cosine (normalized).
- BM25   (bm25.pkl)     — sparse lexical index over tokenized chunk text.
- SQLite (chunks.sqlite)— the source of truth for chunk text + metadata, keyed
                          by chunk_id. Citations resolve through here.

A shared row-ordering invariant ties them together: FAISS row i, BM25 doc i, and
SQLite `ord = i` all refer to the same chunk. That ordering is the contract.
"""
from __future__ import annotations

import json
import pickle
import re
import sqlite3
from pathlib import Path

import numpy as np

from .config import CONFIG
from .schema import Chunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenization for BM25. Deliberately simple and
    deterministic so the sparse index is reproducible."""
    return _TOKEN_RE.findall(text.lower())


# --- Build (ingestion) -----------------------------------------------------
def build_indexes(chunks: list[Chunk], embeddings: np.ndarray) -> None:
    import faiss
    from rank_bm25 import BM25Okapi

    _faiss_path().parent.mkdir(parents=True, exist_ok=True)

    # FAISS — flat inner-product (exact). Corpus is small; no IVF/HNSW needed.
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, str(_faiss_path()))

    # BM25 — tokenize once, persist the fitted index.
    tokenized = [tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(_bm25_path(), "wb") as f:
        pickle.dump({"bm25": bm25, "tokenized_len": len(tokenized)}, f)

    # SQLite — chunk metadata keyed by chunk_id, with `ord` = row order.
    _write_sqlite(chunks)

    # Manifest — model + counts, so retrieval can sanity-check compatibility.
    _meta_path().write_text(
        json.dumps(
            {
                "embedding_model": CONFIG.embedding_model,
                "dim": dim,
                "num_chunks": len(chunks),
                "chunk_size": CONFIG.chunk_size,
                "chunk_overlap": CONFIG.chunk_overlap,
            },
            indent=2,
        )
    )


def _write_sqlite(chunks: list[Chunk]) -> None:
    path = _sqlite_path()
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE chunks (
            ord INTEGER PRIMARY KEY,
            chunk_id TEXT UNIQUE,
            doc_id TEXT,
            source TEXT,
            page INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            text TEXT
        )"""
    )
    conn.execute("CREATE INDEX idx_chunk_id ON chunks(chunk_id)")
    conn.executemany(
        "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                i,
                c.chunk_id,
                c.doc_id,
                c.source,
                c.page,
                c.char_start,
                c.char_end,
                c.text,
            )
            for i, c in enumerate(chunks)
        ],
    )
    conn.commit()
    conn.close()


# --- Load (retrieval) ------------------------------------------------------
class Store:
    """Read-side handle over the three indexes. Loads everything once and keeps
    an in-memory ord->Chunk map for O(1) hydration of retrieval hits."""

    def __init__(self):
        import faiss

        if not _faiss_path().exists():
            raise FileNotFoundError(
                "No index found. Run ingestion first:  python -m scripts.ingest"
            )
        self.index = faiss.read_index(str(_faiss_path()))
        with open(_bm25_path(), "rb") as f:
            self.bm25 = pickle.load(f)["bm25"]
        self.meta = json.loads(_meta_path().read_text())
        self.chunks: list[Chunk] = self._load_chunks()
        self.by_id: dict[str, Chunk] = {c.chunk_id: c for c in self.chunks}

    def _load_chunks(self) -> list[Chunk]:
        conn = sqlite3.connect(_sqlite_path())
        rows = conn.execute(
            "SELECT chunk_id, doc_id, source, page, char_start, char_end, text "
            "FROM chunks ORDER BY ord"
        ).fetchall()
        conn.close()
        return [
            Chunk(
                chunk_id=r[0],
                doc_id=r[1],
                source=r[2],
                page=r[3],
                char_start=r[4],
                char_end=r[5],
                text=r[6],
            )
            for r in rows
        ]

    def __len__(self) -> int:
        return len(self.chunks)

    def chunk_at(self, ordinal: int) -> Chunk:
        return self.chunks[ordinal]

    def get(self, chunk_id: str) -> Chunk | None:
        return self.by_id.get(chunk_id)


# --- Path helpers ----------------------------------------------------------
def _faiss_path() -> Path:
    from .config import FAISS_PATH

    return FAISS_PATH


def _bm25_path() -> Path:
    from .config import BM25_PATH

    return BM25_PATH


def _sqlite_path() -> Path:
    from .config import SQLITE_PATH

    return SQLITE_PATH


def _meta_path() -> Path:
    from .config import META_PATH

    return META_PATH
