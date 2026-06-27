"""Unit tests for the dependency-free core logic: RRF fusion, citation
validation, BM25 tokenization, and the decomposition guard. These run without
any heavy ML deps or network, so they're the fast correctness check.

Run:  python -m pytest tests/ -q     (or)     python tests/test_logic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.schema import Chunk, Retrieved  # noqa: E402
from rag.stores import tokenize  # noqa: E402


def _mk(cid: str, doc: str = "d", text: str = "x") -> Retrieved:
    return Retrieved(
        chunk=Chunk(
            chunk_id=cid, doc_id=doc, source=f"{doc}.md", page=None,
            char_start=0, char_end=len(text), text=text,
        )
    )


def test_tokenize():
    assert tokenize("Hello, RPL-42 World!") == ["hello", "rpl", "42", "world"]
    assert tokenize("") == []


def test_merge_rrf_dedupes_and_ranks():
    from rag.retrieval import merge_rrf

    list_a = [_mk("c1"), _mk("c2"), _mk("c3")]
    list_b = [_mk("c2"), _mk("c4")]
    merged = merge_rrf([list_a, list_b], rrf_k=60)
    ids = [r.chunk_id for r in merged]
    # c2 appears in both lists near the top -> should rank first
    assert ids[0] == "c2"
    # dedupe: every id appears once
    assert len(ids) == len(set(ids)) == 4


def test_citation_validation_strips_hallucinated():
    from rag.generate import AnswerGenerator

    retrieved = [_mk("doc::c00001"), _mk("doc::c00002")]
    gen = AnswerGenerator.__new__(AnswerGenerator)  # no LLM init
    text = "The sky is blue [doc::c00001]. Grass is green [doc::c99999]."
    ans = gen._validate_citations(text, retrieved)

    assert "doc::c99999" not in ans.text          # hallucinated cite stripped
    assert "doc::c00001" in ans.text              # valid cite kept
    assert ans.invalid_citations == ["doc::c99999"]
    assert ans.citation_validity == 0.5           # 1 of 2 cites valid
    assert [r.chunk_id for r in ans.cited] == ["doc::c00001"]


def test_citation_validation_handles_multi_id_brackets():
    from rag.generate import AnswerGenerator

    retrieved = [_mk("a::c1"), _mk("a::c2")]
    gen = AnswerGenerator.__new__(AnswerGenerator)
    text = "Combined fact [a::c1][a::c2]. Bad one [a::c9]."
    ans = gen._validate_citations(text, retrieved)
    assert ans.invalid_citations == ["a::c9"]
    assert round(ans.citation_validity, 3) == round(2 / 3, 3)


def test_retrieval_metrics():
    from eval.dataset import EvalItem
    from eval.metrics import retrieval_metrics

    item = EvalItem(id="x", question="q", ground_truth="g", gold_docs=["d1"], category="simple")
    retrieved = [_mk("d1::c1", doc="d1"), _mk("d2::c1", doc="d2")]
    m = retrieval_metrics(retrieved, item)
    assert m["gold_hit"] == 1.0
    assert m["context_recall_doc"] == 1.0
    assert m["context_precision_doc"] == 0.5


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")
