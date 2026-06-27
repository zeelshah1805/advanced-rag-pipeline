"""Langfuse observability — wired from the start, but fully optional.

If Langfuse keys aren't set (or the package isn't installed) every helper here
becomes a no-op, so the pipeline runs identically with or without tracing. This
keeps the "I think about production cost" story without making it a hard dep.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from .config import CONFIG

_client = None
_init_tried = False


def _get_client():
    global _client, _init_tried
    if _init_tried:
        return _client
    _init_tried = True
    if not CONFIG.langfuse_enabled:
        return None
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=CONFIG.langfuse_public_key,
            secret_key=CONFIG.langfuse_secret_key,
            host=CONFIG.langfuse_host,
        )
    except Exception:  # pragma: no cover - tracing must never break the pipeline
        _client = None
    return _client


class _NullSpan:
    """Stand-in span used when tracing is disabled. Records latency locally so
    the pipeline can still surface per-stage timings in its result `meta`."""

    def __init__(self, name: str):
        self.name = name
        self._t0 = time.perf_counter()
        self.latency_ms = 0.0
        self.payload: dict[str, Any] = {}

    def update(self, **kw: Any) -> None:
        self.payload.update(kw)

    def end(self) -> None:
        self.latency_ms = (time.perf_counter() - self._t0) * 1000


@contextmanager
def span(name: str, trace=None, **inputs: Any):
    """Context manager that yields a span object exposing `.update()` and a
    `.latency_ms`. Works whether or not Langfuse is active."""
    s = _NullSpan(name)
    lf_span = None
    if trace is not None:
        try:
            lf_span = trace.span(name=name, input=inputs or None)
        except Exception:
            lf_span = None
    try:
        yield s
    finally:
        s.end()
        if lf_span is not None:
            try:
                lf_span.update(output=s.payload, metadata={"latency_ms": s.latency_ms})
                lf_span.end()
            except Exception:
                pass


def new_trace(name: str, query: str):
    client = _get_client()
    if client is None:
        return None
    try:
        return client.trace(name=name, input={"query": query})
    except Exception:
        return None


def flush() -> None:
    client = _get_client()
    if client is not None:
        try:
            client.flush()
        except Exception:
            pass
