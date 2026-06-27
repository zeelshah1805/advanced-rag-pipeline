"""Central configuration. All tunables live here so the pipeline is easy to
defend line-by-line. Values come from environment (.env) with sane defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# FAISS and PyTorch each ship an OpenMP runtime; loading both in one process
# crashes with "OMP: Error #111" on Windows/macOS. Allowing the duplicate is the
# documented, safe workaround for inference workloads. Set before either imports.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# We use the PyTorch backend only. Telling transformers to skip TensorFlow/Flax
# avoids importing TF's native libs (flaky on some Windows boxes — the AVX/MSVC
# DLL errors) and cuts import time + the oneDNN log spam. Must precede any
# transformers/sentence-transformers import.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional at runtime
    pass

# Repo paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
SAMPLE_DIR = DATA_DIR / "sample"
STORAGE_DIR = ROOT / "storage"

# Index artifact locations (written by ingestion, read by retrieval) ----------
FAISS_PATH = STORAGE_DIR / "faiss.index"
BM25_PATH = STORAGE_DIR / "bm25.pkl"
SQLITE_PATH = STORAGE_DIR / "chunks.sqlite"
META_PATH = STORAGE_DIR / "meta.json"  # embedding dim, model name, counts


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Config:
    # --- LLM ---
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq"))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )
    ollama_host: str = field(
        default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    )

    # --- Models ---
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    )
    reranker_model: str = field(
        default_factory=lambda: os.getenv(
            "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
    )

    # --- Chunking ---
    chunk_size: int = field(default_factory=lambda: _int("CHUNK_SIZE", 500))
    chunk_overlap: int = field(default_factory=lambda: _int("CHUNK_OVERLAP", 80))

    # --- Retrieval ---
    top_k_dense: int = field(default_factory=lambda: _int("TOP_K_DENSE", 30))
    top_k_sparse: int = field(default_factory=lambda: _int("TOP_K_SPARSE", 30))
    rrf_k: int = field(default_factory=lambda: _int("RRF_K", 60))
    candidates: int = field(default_factory=lambda: _int("CANDIDATES", 30))
    final_k: int = field(default_factory=lambda: _int("FINAL_K", 6))
    naive_k: int = field(default_factory=lambda: _int("NAIVE_K", 6))

    # --- Observability ---
    langfuse_public_key: str = field(
        default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY", "")
    )
    langfuse_secret_key: str = field(
        default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY", "")
    )
    langfuse_host: str = field(
        default_factory=lambda: os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


CONFIG = Config()
