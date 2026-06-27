"""Deterministic retrieval metrics — no LLM, no cost, no flakiness.

These don't replace RAGAS; they complement it. Because our eval set records the
gold *source document(s)* per question, we can measure retrieval quality
directly and cheaply:

- gold_hit@k        : did at least one retrieved chunk come from a gold doc?
- context_recall_doc: fraction of gold docs that appear in the retrieved context.
- context_precision_doc: fraction of retrieved chunks that come from a gold doc.

They map onto the same failure modes RAGAS names (recall vs precision) but are
free to run, so they're the fast inner loop while iterating on retrieval.
"""
from __future__ import annotations

from statistics import mean

from rag.schema import Retrieved

from .dataset import EvalItem


def gold_hit(retrieved: list[Retrieved], gold_docs: list[str]) -> float:
    gold = set(gold_docs)
    return 1.0 if any(r.chunk.doc_id in gold for r in retrieved) else 0.0


def context_recall_doc(retrieved: list[Retrieved], gold_docs: list[str]) -> float:
    if not gold_docs:
        return 1.0
    gold = set(gold_docs)
    found = {r.chunk.doc_id for r in retrieved} & gold
    return len(found) / len(gold)


def context_precision_doc(retrieved: list[Retrieved], gold_docs: list[str]) -> float:
    if not retrieved:
        return 0.0
    gold = set(gold_docs)
    relevant = sum(1 for r in retrieved if r.chunk.doc_id in gold)
    return relevant / len(retrieved)


def aggregate(per_item: list[dict]) -> dict:
    """Mean each numeric metric across items, ignoring None."""
    if not per_item:
        return {}
    keys = [k for k, v in per_item[0].items() if isinstance(v, (int, float))]
    return {k: round(mean(d[k] for d in per_item), 4) for k in keys}


def retrieval_metrics(retrieved: list[Retrieved], item: EvalItem) -> dict:
    return {
        "gold_hit": gold_hit(retrieved, item.gold_docs),
        "context_recall_doc": context_recall_doc(retrieved, item.gold_docs),
        "context_precision_doc": context_precision_doc(retrieved, item.gold_docs),
    }
