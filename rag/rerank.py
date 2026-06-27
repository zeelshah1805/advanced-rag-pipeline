"""Cross-encoder reranking.

Bi-encoder retrieval (FAISS/BM25) scores query and doc independently — fast and
recall-oriented but noisy. The cross-encoder reads query+doc *together*, so it's
far more precise. It's expensive, so it only ever sees the ~30 candidates that
retrieval already narrowed to, then we keep the top `final_k`.
"""
from __future__ import annotations

from functools import lru_cache

from .config import CONFIG
from .schema import Retrieved


class Reranker:
    def __init__(self, model_name: str | None = None):
        from sentence_transformers import CrossEncoder  # lazy: heavy import

        self.model_name = model_name or CONFIG.reranker_model
        self.model = CrossEncoder(self.model_name)

    def rerank(
        self, query: str, candidates: list[Retrieved], top_k: int | None = None
    ) -> list[Retrieved]:
        top_k = top_k or CONFIG.final_k
        if not candidates:
            return []
        pairs = [(query, r.chunk.text) for r in candidates]
        scores = self.model.predict(pairs, show_progress_bar=False)
        for r, s in zip(candidates, scores):
            r.rerank_score = float(s)
            r.score = float(s)
        ranked = sorted(candidates, key=lambda r: r.rerank_score, reverse=True)
        return ranked[:top_k]


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker()
