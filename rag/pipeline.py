"""Pipeline orchestrator.

One class, four toggles. Each toggle maps to one rung of the ablation ladder, so
the *same* code path produces naive, +hybrid, +rerank, and +decomposition — the
eval harness just flips flags. That shared path is what makes the ablation an
honest comparison rather than four different programs.

    PipelineConfig(hybrid=False, rerank=False, decompose=False)  -> Naive
    PipelineConfig(hybrid=True)                                  -> + Hybrid
    PipelineConfig(hybrid=True, rerank=True)                     -> + Reranker
    PipelineConfig(hybrid=True, rerank=True, decompose=True)     -> + Decomposition
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import CONFIG
from .decompose import QueryDecomposer
from .generate import AnswerGenerator
from .observability import flush, new_trace, span
from .rerank import get_reranker
from .retrieval import HybridRetriever, merge_rrf
from .schema import Answer, Retrieved
from .stores import Store


@dataclass
class PipelineConfig:
    hybrid: bool = True        # BM25 + dense + RRF (off => naive dense top-k)
    rerank: bool = True        # cross-encoder rerank of fused candidates
    decompose: bool = True     # multi-hop gate + sub-question retrieval merge
    candidates: int = CONFIG.candidates  # how many to fuse before rerank
    final_k: int = CONFIG.final_k        # context size handed to the generator

    @classmethod
    def naive(cls) -> "PipelineConfig":
        return cls(hybrid=False, rerank=False, decompose=False, final_k=CONFIG.naive_k)

    def label(self) -> str:
        if not self.hybrid and not self.rerank and not self.decompose:
            return "naive"
        parts = ["hybrid"] if self.hybrid else ["dense"]
        if self.rerank:
            parts.append("rerank")
        if self.decompose:
            parts.append("decomp")
        return "+".join(parts)


class RAGPipeline:
    def __init__(self, store: Store | None = None, lazy_llm: bool = True):
        self.store = store or Store()
        self.retriever = HybridRetriever(self.store)
        self._reranker = None
        self._decomposer = None
        self._generator = None
        if not lazy_llm:
            _ = self.generator  # force init (surfaces missing GROQ_API_KEY early)

    # lazy components so retrieval-only / offline use doesn't require an LLM key
    @property
    def reranker(self):
        if self._reranker is None:
            self._reranker = get_reranker()
        return self._reranker

    @property
    def decomposer(self) -> QueryDecomposer:
        if self._decomposer is None:
            self._decomposer = QueryDecomposer()
        return self._decomposer

    @property
    def generator(self) -> AnswerGenerator:
        if self._generator is None:
            self._generator = AnswerGenerator()
        return self._generator

    # --- retrieval (no LLM unless decompose=True) -------------------------
    def retrieve(self, query: str, cfg: PipelineConfig, trace=None) -> tuple[list[Retrieved], list[str]]:
        sub_questions: list[str] = []

        if cfg.decompose:
            with span("decompose", trace, query=query) as s:
                sub_questions = self.decomposer.decompose(query)
                s.update(sub_questions=sub_questions)

        queries = sub_questions if sub_questions else [query]

        with span("retrieve", trace, queries=queries, hybrid=cfg.hybrid) as s:
            per_query: list[list[Retrieved]] = []
            for q in queries:
                if cfg.hybrid:
                    hits = self.retriever.hybrid(
                        q, k=cfg.candidates,
                        via_subquery=q if sub_questions else None,
                    )
                else:
                    hits = self.retriever.naive(q, k=cfg.final_k)
                per_query.append(hits)
            candidates = merge_rrf(per_query) if len(per_query) > 1 else per_query[0]
            s.update(num_candidates=len(candidates))

        if cfg.rerank:
            with span("rerank", trace, n_in=len(candidates)) as s:
                candidates = self.reranker.rerank(query, candidates, top_k=cfg.final_k)
                s.update(n_out=len(candidates))
        else:
            candidates = candidates[: cfg.final_k]

        return candidates, sub_questions

    # --- full answer ------------------------------------------------------
    def answer(self, query: str, cfg: PipelineConfig | None = None) -> Answer:
        cfg = cfg or PipelineConfig()
        trace = new_trace(name=f"rag::{cfg.label()}", query=query)

        context, sub_questions = self.retrieve(query, cfg, trace=trace)

        with span("generate", trace, n_context=len(context)) as s:
            ans = self.generator.generate(query, context)
            s.update(
                citation_validity=ans.citation_validity,
                invalid_citations=ans.invalid_citations,
            )

        ans.sub_questions = sub_questions
        ans.meta["config"] = cfg.label()
        if trace is not None:
            try:
                trace.update(output={"answer": ans.text[:2000]})
            except Exception:
                pass
            flush()
        return ans
