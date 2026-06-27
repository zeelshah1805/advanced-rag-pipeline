"""Ablation driver — the single most credible artifact in the project.

Runs the same pipeline at four rungs (naive -> +hybrid -> +rerank -> +decomp)
over the held-out eval set, scoring each with:
  - deterministic retrieval metrics (always, free), and
  - RAGAS metrics (faithfulness/answer_relevancy/context_precision/context_recall)
    when a judge is configured.

Writes a JSON dump and a Markdown table to eval/results/. Do NOT hand-edit the
numbers — a fabricated table an interviewer can poke a hole in is worse than
none. Report real `n` and per-category breakdowns; own the small-sample caveat.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from rag.pipeline import PipelineConfig, RAGPipeline
from rag.stores import Store

from .dataset import EvalItem, load_eval_set
from .metrics import aggregate, retrieval_metrics
from .ragas_eval import score_with_ragas

RESULTS_DIR = Path(__file__).resolve().parent / "results"

LADDER: list[tuple[str, PipelineConfig]] = [
    ("Naive (vector top-k)", PipelineConfig.naive()),
    ("+ Hybrid (RRF)", PipelineConfig(hybrid=True, rerank=False, decompose=False)),
    ("+ Reranker", PipelineConfig(hybrid=True, rerank=True, decompose=False)),
    ("+ Decomposition", PipelineConfig(hybrid=True, rerank=True, decompose=True)),
]


def _run_config(
    pipe: RAGPipeline, cfg: PipelineConfig, items: list[EvalItem], with_ragas: bool
) -> dict:
    per_item = []
    ragas_samples = []
    cat_metrics: dict[str, list[dict]] = defaultdict(list)

    for it in items:
        ans = pipe.answer(it.question, cfg)
        rm = retrieval_metrics(ans.retrieved, it)
        rm["citation_validity"] = ans.citation_validity
        per_item.append(rm)
        cat_metrics[it.category].append(rm)
        ragas_samples.append(
            {
                "question": it.question,
                "contexts": [r.chunk.text for r in ans.retrieved],
                "answer": ans.text,
                "ground_truth": it.ground_truth,
            }
        )

    summary = aggregate(per_item)
    by_category = {c: aggregate(v) for c, v in cat_metrics.items()}

    ragas_scores = None
    if with_ragas:
        ragas_scores = score_with_ragas(ragas_samples)

    return {"retrieval": summary, "by_category": by_category, "ragas": ragas_scores}


def run(no_ragas: bool = False, limit: int | None = None, model: str | None = None) -> dict:
    if model:
        # Override for this run only (both generation and the RAGAS judge read
        # CONFIG.groq_model live). Lets us eval on a cheaper/higher-quota model
        # than the 70b "product" default without touching .env.
        from rag.config import CONFIG

        print(f"[ablation] overriding model: {CONFIG.groq_model} -> {model}")
        CONFIG.groq_model = model

    items = load_eval_set()
    if limit:
        items = items[:limit]
    print(f"[ablation] {len(items)} eval questions; building pipeline ...")

    store = Store()
    pipe = RAGPipeline(store=store)

    results: dict[str, dict] = {}
    for label, cfg in LADDER:
        print(f"[ablation] running config: {label} ({cfg.label()}) ...")
        t0 = time.perf_counter()
        results[label] = _run_config(pipe, cfg, items, with_ragas=not no_ragas)
        results[label]["seconds"] = round(time.perf_counter() - t0, 1)
        print(f"           done in {results[label]['seconds']}s -> {results[label]['retrieval']}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"n": len(items), "configs": results}
    (RESULTS_DIR / "ablation.json").write_text(json.dumps(payload, indent=2))
    md = render_markdown(payload)
    (RESULTS_DIR / "ablation.md").write_text(md, encoding="utf-8")
    print(f"\n[ablation] wrote {RESULTS_DIR/'ablation.json'} and ablation.md\n")
    print(md)
    return payload


def render_markdown(payload: dict) -> str:
    n = payload["n"]
    configs = payload["configs"]
    has_ragas = any(c.get("ragas") for c in configs.values())

    lines = [f"# RAG Ablation Results (n={n})", ""]

    if has_ragas:
        lines += [
            "## RAGAS metrics",
            "",
            "| Config | ctx_recall | ctx_precision | faithfulness | ans_relevancy |",
            "|---|---|---|---|---|",
        ]
        for label, c in configs.items():
            r = c.get("ragas") or {}
            lines.append(
                f"| {label} | {_fmt(r.get('context_recall'))} | "
                f"{_fmt(r.get('context_precision'))} | {_fmt(r.get('faithfulness'))} | "
                f"{_fmt(r.get('answer_relevancy'))} |"
            )
        lines.append("")

    lines += [
        "## Retrieval metrics (deterministic, gold-source based)",
        "",
        "| Config | gold_hit | ctx_recall_doc | ctx_precision_doc | citation_validity | secs |",
        "|---|---|---|---|---|---|",
    ]
    for label, c in configs.items():
        m = c["retrieval"]
        lines.append(
            f"| {label} | {_fmt(m.get('gold_hit'))} | {_fmt(m.get('context_recall_doc'))} | "
            f"{_fmt(m.get('context_precision_doc'))} | {_fmt(m.get('citation_validity'))} | "
            f"{c.get('seconds','-')} |"
        )
    lines.append("")
    lines.append(
        f"_n={n}. Small sample — read these as directional, per-category, not a "
        "single inflated average._"
    )
    return "\n".join(lines)


def _fmt(v) -> str:
    return f"{v:.3f}" if isinstance(v, (int, float)) else "—"


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the RAG ablation harness.")
    ap.add_argument("--no-ragas", action="store_true", help="skip RAGAS (retrieval metrics only)")
    ap.add_argument("--limit", type=int, default=None, help="evaluate only the first N questions")
    ap.add_argument(
        "--model",
        default=None,
        help="override the Groq model for this run (e.g. llama-3.1-8b-instant "
        "to stay under the free daily token cap)",
    )
    args = ap.parse_args()
    run(no_ragas=args.no_ragas, limit=args.limit, model=args.model)


if __name__ == "__main__":
    main()
