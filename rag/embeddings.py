"""Embedding model wrapper around sentence-transformers bge-small.

bge models want a query instruction prefix for retrieval; passages are embedded
raw. We normalize so FAISS inner-product == cosine similarity.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import CONFIG

# bge-* retrieval instruction (recommended by the model card)
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class Embedder:
    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer  # lazy: heavy import

        self.model_name = model_name or CONFIG.embedding_model
        self.model = SentenceTransformer(self.model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed_passages(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 256,
            convert_to_numpy=True,
        ).astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        vec = self.model.encode(
            _QUERY_INSTRUCTION + query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")
        return vec.reshape(1, -1)


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder()
