---
title: Advanced RAG Pipeline
emoji: 🔎
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.36.0
app_file: app/streamlit_app.py
pinned: false
---

# Advanced RAG Pipeline

A production-grade Retrieval-Augmented Generation system that **beats naive RAG**
— and proves it with a real ablation table, not vibes.

**[▶ Live demo on Hugging Face Spaces](https://huggingface.co/spaces/zeelshah1805/advanced-rag-pipeline)**

Naive RAG (`embed → top-k → stuff into prompt`) breaks on keyword/acronym
queries, multi-hop questions, and long noisy contexts. This project engineers
past each of those failure modes and measures the lift from every component:

- **Hybrid retrieval** — dense embeddings **+** sparse BM25, fused with
  Reciprocal Rank Fusion (RRF). Fixes pure-vector retrieval missing exact
  keywords, names, codes, and acronyms.
- **Query decomposition** — a multi-hop *gate* splits complex questions into
  sub-questions, retrieves for each, and merges. Fixes single-vector retrieval
  that can't satisfy "compare X and Y."
- **Cross-encoder reranking** — re-scores fused candidates so the *most*
  relevant chunks land in a small, clean context. Fixes bi-encoder noise.
- **Validated citations** — every answer cites `[chunk_id]`s; hallucinated cites
  are stripped and counted as a `citation_validity` metric. Makes answers
  verifiable.
- **RAGAS evaluation** — a held-out question set scored on faithfulness, answer
  relevancy, context precision, and context recall, run as an **ablation**:
  naive → +hybrid → +rerank → +decomposition.

**The whole stack is free and open source.** Models run on Groq's free hosted
tier with a fully-offline Ollama fallback; everything else is local OSS (FAISS,
BM25, sentence-transformers). Zero cost to run.

---

## Results (ablation)

_n=20 questions across 4 categories (factoid, multi-hop, comparison, technical).
Corpus: 30 documents → 55 chunks; k=6, so retrieval is genuinely selective._

### Deterministic retrieval metrics (gold-source based, no LLM judge)

| Config | ctx_recall_doc ↑ | ctx_precision_doc ↑ | citation_validity |
|---|---|---|---|
| Naive (vector top-k) | 0.900 | 0.367 | **1.000** |
| + Hybrid (RRF) | 0.958 | **0.408** | **1.000** |
| + Reranker | **1.000** | **0.408** | 0.957 |
| + Decomposition | **1.000** | **0.408** | 0.957 |

**What it shows:**
- Hybrid retrieval lifts context recall 0.900 → 0.958 and precision 0.367 → 0.408 — BM25's exact-match leg finds docs that dense embeddings missed (keyword codes, abbreviations, acronyms).
- Reranker pushes recall to **100%** across all 20 questions — no gold source left out of the top-6 window.
- Decomposition holds the full-pipeline gains; its lift shows on harder multi-hop questions (see `eval/results/ablation.json` for per-category breakdown).

### RAGAS metrics (LLM-judged, `llama-3.1-8b-instant` judge)

| Config | ctx_recall | ctx_precision | faithfulness | ans_relevancy |
|---|---|---|---|---|
| Naive (vector top-k) | — | — | — | 0.878 |
| + Hybrid (RRF) | **1.000** | **0.967** | — | **0.883** |
| + Reranker | — | — | — | 0.863 |
| + Decomposition | — | — | — | 0.863 |

_`—` = NaN: the 8b judge's output format wasn't reliably parsed by RAGAS 0.2.x for those configs. `answer_relevancy` (embedding-based) was stable across all. The deterministic table is the reliable headline._

---

## Architecture

```
query ─► Query Decomposer (LLM, gated)  ─► [sub-q1, sub-q2, ...]
              │ (for each sub-question)
              ▼
        Hybrid Retriever
          BM25 ─┐
                ├─ Reciprocal Rank Fusion ─► ~30 candidates (deduped)
        dense ─┘
              ▼
        Cross-Encoder Reranker  ─► top 5–8 clean, ordered chunks
              ▼
        Answer Generator (LLM)  ─► answer with inline [chunk_id] citations
              ▼
        Citation Validator      ─► strip hallucinated cites, score validity
              ▼
        answer + [sources]

   Offline: RAGAS ablation harness over a held-out Q/A set
   Observability: Langfuse traces every stage (latency + retrieved IDs)
```

**Ingestion (one-time):** load docs → chunk (recursive, ~500 tokens, ~80
overlap, keeping `doc_id` / `page` / `char_span` on every chunk) → embed with
`bge-small` → write vectors to FAISS, text to a BM25 index + SQLite. Chunk
metadata is what makes citations possible, so it's a first-class field.

---

## Quickstart

```bash
# 1. Install (Python 3.11+)
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env    # add your free GROQ_API_KEY from console.groq.com

# 3. Ingest (index is pre-built in storage/ for the sample corpus)
python -m scripts.ingest                 # re-ingest if you change the corpus

# 4. Ask
python -m scripts.ask "What does RPL stand for?"
python -m scripts.ask --naive "Compare Scale vs Enterprise retention"

# 5. Run the ablation
python -m eval.run_ablation --model llama-3.1-8b-instant

# 6. Demo UI
streamlit run app/streamlit_app.py
```

### Install troubleshooting

- **pip backtracks into langchain 1.x** — install into a fresh venv; the pins in `requirements.txt` keep the core on 0.2.x. RAGAS lives in `requirements-eval.txt` so the core install stays clean.
- **`PermissionError` on Windows Scripts** — use a venv or `pip install --user -r requirements-eval.txt`.
- **`OMP: Error #111`** — FAISS + PyTorch OpenMP clash; handled via `KMP_DUPLICATE_LIB_OK=TRUE` in `rag/config.py`.
- **`Failed to import transformers.modeling_tf_utils`** — handled via `USE_TF=0` in `rag/config.py`.

---

## Repo layout

```
rag/
  config.py        # all tunables, env-driven
  schema.py        # Chunk / Retrieved / Answer dataclasses
  llm.py           # model-agnostic client (Groq + Ollama), retry/backoff
  observability.py # Langfuse spans (no-op if unconfigured)
  loaders.py       # PDF/txt/md loading + recursive chunking with offsets
  embeddings.py    # bge-small wrapper (query instruction + normalization)
  stores.py        # FAISS + BM25 + SQLite, tied by a row-ordering invariant
  ingest.py        # load → chunk → embed → build indexes
  retrieval.py     # dense, sparse, hybrid RRF, multi-query merge
  rerank.py        # cross-encoder reranker
  decompose.py     # multi-hop gate + sub-question generation
  generate.py      # citation-contract prompt + post-hoc cite validation
  pipeline.py      # orchestrator with ablation toggles (naive ↔ full)
eval/
  eval_set.jsonl   # 20 held-out Q/A with gold source docs, 4 categories
  metrics.py       # deterministic retrieval metrics (free, no LLM)
  ragas_eval.py    # RAGAS judge wrapper (best-effort, free Groq/Ollama)
  run_ablation.py  # driver → eval/results/ablation.{json,md}
storage/           # pre-built FAISS + BM25 + SQLite indexes (sample corpus)
data/sample/       # 30-doc self-contained corpus (Nimbus data platform docs)
scripts/           # ingest.py, ask.py CLIs
app/               # streamlit_app.py (sources panel + citation validity badge)
tests/             # dependency-free unit tests (RRF, citation validation, …)
```

---

## Design tradeoffs

| Decision | Why | Alternative |
|---|---|---|
| **RRF** for fusion | Rank-based, no score-normalization fragility between cosine and BM25 magnitudes | Weighted score fusion (needs careful normalization, brittle) |
| **Cross-encoder** rerank | Reads query+doc *together* → precise; only runs on ~30 candidates | Cohere Rerank (managed, generous free tier; one-line swap) |
| **Gated** decomposition | Decomposing simple queries adds latency/cost and dilutes retrieval | Always-decompose (measurably worse on single-hop) |
| **FAISS flat** | Exact search, zero infra at this corpus size | IVF/HNSW or Qdrant/pgvector at 10M+ docs |
| **bge-small** local | Strong MTEB scores, tiny, CPU-friendly, free | Paid embedding APIs |
| Citation **validation** | Trust: strip hallucinated cites, report validity % | Trust the model |

---

## Tests

```bash
python tests/test_logic.py        # or: python -m pytest tests/ -q
```

Covers: RRF fusion + dedupe, citation validation (hallucination stripping),
BM25 tokenization, deterministic retrieval metrics — no network, no GPU.
