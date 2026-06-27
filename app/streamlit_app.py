"""Streamlit UI — a clickable demo with a sources panel.

Run:  streamlit run app/streamlit_app.py

The sources panel is the point: every answer shows the exact chunks it used,
their source doc + page, and the citation-validity score, so the demo *shows*
that the answer is grounded rather than asserting it.
"""
from __future__ import annotations

import sys
from pathlib import Path

# allow `streamlit run app/streamlit_app.py` from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from rag.pipeline import PipelineConfig, RAGPipeline  # noqa: E402
from rag.stores import Store  # noqa: E402

st.set_page_config(page_title="Advanced RAG", page_icon="🔎", layout="wide")


@st.cache_resource(show_spinner="Loading index + models …")
def get_pipeline():
    return RAGPipeline(store=Store())


st.title("🔎 Advanced RAG — hybrid retrieval · rerank · cited answers")

with st.sidebar:
    st.header("Pipeline")
    mode = st.radio(
        "Configuration",
        ["Full pipeline", "Naive baseline", "Custom"],
        help="Naive = vector top-k only. Full = hybrid + rerank + decomposition.",
    )
    if mode == "Custom":
        hybrid = st.checkbox("Hybrid retrieval (BM25 + dense, RRF)", value=True)
        rerank = st.checkbox("Cross-encoder reranker", value=True)
        decompose = st.checkbox("Query decomposition (multi-hop gate)", value=True)
        cfg = PipelineConfig(hybrid=hybrid, rerank=rerank, decompose=decompose)
    elif mode == "Naive baseline":
        cfg = PipelineConfig.naive()
    else:
        cfg = PipelineConfig()
    st.caption(f"Active config: `{cfg.label()}`")
    st.divider()
    st.caption(
        "Tip: try a keyword/acronym query (e.g. *What does RPL stand for?*) and a "
        "multi-hop one (e.g. *Compare Scale vs Enterprise retention*) to see hybrid "
        "and decomposition earn their keep."
    )

query = st.text_input("Ask a question about the corpus", placeholder="e.g. What does RPL stand for?")

if query:
    try:
        pipe = get_pipeline()
    except FileNotFoundError as e:
        st.error(f"{e}")
        st.stop()

    with st.spinner("Retrieving and generating …"):
        ans = pipe.answer(query, cfg)

    col_ans, col_src = st.columns([3, 2])

    with col_ans:
        st.subheader("Answer")
        if ans.sub_questions:
            with st.expander("🧩 Decomposed sub-questions", expanded=False):
                for q in ans.sub_questions:
                    st.markdown(f"- {q}")
        st.markdown(ans.text)

        vbadge = "✅" if ans.citation_validity >= 0.999 else "⚠️"
        st.metric("Citation validity", f"{ans.citation_validity:.0%}", help=(
            "Fraction of the model's [chunk_id] citations that point to a chunk we "
            "actually retrieved. Hallucinated cites are stripped."
        ))
        if ans.invalid_citations:
            st.caption(f"{vbadge} stripped invalid cites: {ans.invalid_citations}")

    with col_src:
        st.subheader("Sources")
        shown = ans.cited or ans.retrieved
        if not shown:
            st.caption("No sources retrieved.")
        for r in shown:
            c = r.chunk
            loc = c.source + (f", p.{c.page}" if c.page is not None else "")
            score = (
                f"rerank={r.rerank_score:.2f}" if r.rerank_score is not None
                else f"rrf={r.rrf_score:.3f}" if r.rrf_score is not None
                else f"score={r.score:.3f}"
            )
            with st.expander(f"[{c.chunk_id}] · {loc} · {score}"):
                if r.via_subquery:
                    st.caption(f"retrieved via sub-question: {r.via_subquery}")
                st.write(c.text)
