"""Retrieval: dense (FAISS), sparse (BM25), and hybrid via Reciprocal Rank
Fusion.

RRF is rank-based: score(d) = sum over retrievers of 1/(k + rank_d). No score
normalization between cosine and BM25 magnitudes — that fragility is exactly
what RRF avoids, which is why it's the expected answer for hybrid fusion.
"""
from __future__ import annotations

import numpy as np

from .config import CONFIG
from .embeddings import get_embedder
from .schema import Retrieved
from .stores import Store, tokenize


class HybridRetriever:
    def __init__(self, store: Store | None = None):
        self.store = store or Store()
        self.embedder = get_embedder()

    # --- single-mode retrieval --------------------------------------------
    def dense(self, query: str, k: int | None = None) -> list[tuple[int, float]]:
        k = k or CONFIG.top_k_dense
        qvec = self.embedder.embed_query(query)
        scores, idxs = self.store.index.search(qvec, min(k, len(self.store)))
        return [
            (int(i), float(s))
            for i, s in zip(idxs[0], scores[0])
            if i != -1
        ]

    def sparse(self, query: str, k: int | None = None) -> list[tuple[int, float]]:
        k = k or CONFIG.top_k_sparse
        scores = self.store.bm25.get_scores(tokenize(query))
        if len(scores) == 0:
            return []
        top = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in top if scores[i] > 0]

    # --- fusion ------------------------------------------------------------
    def hybrid(
        self,
        query: str,
        k: int | None = None,
        rrf_k: int | None = None,
        via_subquery: str | None = None,
    ) -> list[Retrieved]:
        """Dense + sparse, fused with RRF. Returns up to `k` candidates carrying
        their dense/sparse ranks and fused score for debuggability."""
        k = k or CONFIG.candidates
        rrf_k = rrf_k or CONFIG.rrf_k

        dense_hits = self.dense(query)
        sparse_hits = self.sparse(query)

        dense_rank = {idx: r for r, (idx, _) in enumerate(dense_hits)}
        sparse_rank = {idx: r for r, (idx, _) in enumerate(sparse_hits)}

        fused: dict[int, float] = {}
        for idx, r in dense_rank.items():
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + r)
        for idx, r in sparse_rank.items():
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + r)

        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
        results: list[Retrieved] = []
        for idx, rrf_score in ordered:
            chunk = self.store.chunk_at(idx)
            results.append(
                Retrieved(
                    chunk=chunk,
                    score=rrf_score,
                    dense_rank=dense_rank.get(idx),
                    sparse_rank=sparse_rank.get(idx),
                    rrf_score=rrf_score,
                    via_subquery=via_subquery,
                )
            )
        return results

    # --- naive baseline (the control group) -------------------------------
    def naive(self, query: str, k: int | None = None) -> list[Retrieved]:
        """Pure dense top-k. This is the baseline the full pipeline must beat."""
        k = k or CONFIG.naive_k
        hits = self.dense(query, k=k)
        return [
            Retrieved(
                chunk=self.store.chunk_at(idx),
                score=score,
                dense_rank=rank,
            )
            for rank, (idx, score) in enumerate(hits)
        ]


def merge_rrf(result_lists: list[list[Retrieved]], rrf_k: int | None = None) -> list[Retrieved]:
    """Merge several already-ranked result lists (e.g. one per sub-question) into
    a single ranked list via RRF, deduping on chunk_id and keeping the best
    provenance. Used by query decomposition."""
    rrf_k = rrf_k or CONFIG.rrf_k
    fused: dict[str, float] = {}
    best: dict[str, Retrieved] = {}
    best_rank: dict[str, int] = {}
    for results in result_lists:
        for rank, r in enumerate(results):
            cid = r.chunk_id
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (rrf_k + rank)
            # keep the provenance from the list where this chunk ranked highest
            if cid not in best_rank or rank < best_rank[cid]:
                best_rank[cid] = rank
                best[cid] = r
    ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
    out = []
    for cid, score in ordered:
        r = best[cid]
        r.rrf_score = score
        r.score = score
        out.append(r)
    return out
