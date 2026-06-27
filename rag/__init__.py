"""Advanced RAG pipeline package.

Public surface kept small on purpose — the orchestrator (`pipeline.RAGPipeline`)
is the one entry point most code needs.
"""
from .config import CONFIG, Config

__all__ = ["CONFIG", "Config"]
