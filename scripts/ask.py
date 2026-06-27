"""CLI: ask a question against the indexed corpus.

  python -m scripts.ask "What is the max retention on the Scale plan?"
  python -m scripts.ask --naive "..."        # run the naive baseline instead
  python -m scripts.ask --no-rerank "..."    # ablate a single component
"""
from __future__ import annotations

import argparse

from rag.pipeline import PipelineConfig, RAGPipeline


def main() -> None:
    ap = argparse.ArgumentParser(description="Ask the RAG pipeline a question.")
    ap.add_argument("question", help="the question to answer")
    ap.add_argument("--naive", action="store_true", help="use the naive baseline")
    ap.add_argument("--no-hybrid", action="store_true", help="disable hybrid retrieval")
    ap.add_argument("--no-rerank", action="store_true", help="disable reranking")
    ap.add_argument("--no-decompose", action="store_true", help="disable decomposition")
    args = ap.parse_args()

    if args.naive:
        cfg = PipelineConfig.naive()
    else:
        cfg = PipelineConfig(
            hybrid=not args.no_hybrid,
            rerank=not args.no_rerank,
            decompose=not args.no_decompose,
        )

    pipe = RAGPipeline()
    ans = pipe.answer(args.question, cfg)

    print(f"\n=== config: {cfg.label()} ===\n")
    if ans.sub_questions:
        print("Sub-questions:")
        for q in ans.sub_questions:
            print(f"  - {q}")
        print()
    print(ans.text)
    print("\n--- Sources ---")
    for r in ans.cited or ans.retrieved:
        c = r.chunk
        loc = c.source + (f", p.{c.page}" if c.page is not None else "")
        print(f"  [{c.chunk_id}] {loc}")
    print(
        f"\ncitation_validity={ans.citation_validity}  "
        f"invalid={ans.invalid_citations}  context_size={len(ans.retrieved)}"
    )


if __name__ == "__main__":
    main()
