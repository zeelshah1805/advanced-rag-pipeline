"""Core data types shared across ingestion, retrieval, and generation.

`Chunk.metadata` (doc_id, page, char_span) is what makes citations possible,
so it is a first-class field, not an afterthought.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Chunk:
    chunk_id: str          # stable id, e.g. "doc12::c0007" — this is what gets cited
    doc_id: str            # source document id (filename stem)
    source: str            # human-readable source path/name
    page: int | None       # page number (PDFs) or None
    char_start: int        # offset into the source document text
    char_end: int
    text: str

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Retrieved:
    """A chunk that came back from retrieval, carrying its provenance scores so
    we can debug *why* it ranked where it did."""

    chunk: Chunk
    score: float = 0.0
    dense_rank: int | None = None
    sparse_rank: int | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    # which sub-question pulled it in (decomposition); None == original query
    via_subquery: str | None = None

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id


@dataclass
class Answer:
    text: str
    cited: list[Retrieved] = field(default_factory=list)      # validated, used
    retrieved: list[Retrieved] = field(default_factory=list)  # full context shown
    sub_questions: list[str] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    citation_validity: float = 1.0   # fraction of cited ids that were real
    meta: dict[str, Any] = field(default_factory=dict)
