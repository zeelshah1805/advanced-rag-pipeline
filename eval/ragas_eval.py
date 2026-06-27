"""RAGAS metrics wrapper.

Scores the four core RAGAS metrics — faithfulness, answer_relevancy,
context_precision, context_recall — using the *same* free LLM (Groq/Ollama) and
local bge embeddings the pipeline uses, so the judge costs nothing extra.

Everything here is best-effort: RAGAS pulls in a lot of optional deps and its
API drifts between versions. If anything fails to import or configure, the
caller falls back to the deterministic retrieval metrics in `metrics.py`, and
the ablation still produces a real (if smaller) table.
"""
from __future__ import annotations

from typing import Any

from rag.config import CONFIG


class _LocalEmbeddings:
    """Minimal langchain-Embeddings-compatible adapter over our bge model, so
    RAGAS's metrics that need embeddings reuse the same local model (free)."""

    def __init__(self):
        from rag.embeddings import get_embedder

        self._e = get_embedder()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._e.embed_passages(list(texts)).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._e.embed_query(text)[0].tolist()


def _build_judge() -> tuple[Any, Any] | None:
    """Return (ragas_llm, ragas_embeddings) or None if unavailable."""
    try:
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
    except Exception:
        return None

    # Chat model: prefer Groq, fall back to Ollama, matching the pipeline.
    chat = None
    if CONFIG.llm_provider.lower() == "groq" and CONFIG.groq_api_key:
        try:
            from langchain_groq import ChatGroq

            chat = ChatGroq(model=CONFIG.groq_model, api_key=CONFIG.groq_api_key, temperature=0)
        except Exception:
            chat = None
    if chat is None:
        try:
            from langchain_community.chat_models import ChatOllama

            chat = ChatOllama(model=CONFIG.ollama_model, base_url=CONFIG.ollama_host, temperature=0)
        except Exception:
            chat = None
    if chat is None:
        return None

    try:
        llm = LangchainLLMWrapper(chat)
        emb = LangchainEmbeddingsWrapper(_LocalEmbeddings())
        return llm, emb
    except Exception:
        return None


def ragas_available() -> bool:
    return _build_judge() is not None


def score_with_ragas(samples: list[dict]) -> dict | None:
    """`samples`: list of {question, contexts: list[str], answer, ground_truth}.
    Returns {metric: mean_score} or None if RAGAS can't run."""
    judge = _build_judge()
    if judge is None:
        return None
    llm, emb = judge

    try:
        from ragas import EvaluationDataset, evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except Exception:
        return None

    try:
        dataset = EvaluationDataset.from_list(
            [
                {
                    "user_input": s["question"],
                    "retrieved_contexts": s["contexts"],
                    "response": s["answer"],
                    "reference": s["ground_truth"],
                }
                for s in samples
            ]
        )
        metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
        result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=emb)
        df = result.to_pandas()
        out: dict[str, float] = {}
        for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            if m in df.columns:
                val = df[m].dropna().mean()
                out[m] = round(float(val), 4)
        return out or None
    except Exception as e:  # noqa: BLE001
        print(f"[ragas] scoring failed, falling back to retrieval metrics: {e}")
        return None
