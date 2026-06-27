"""Query decomposition with a multi-hop gate.

The gate is the senior move: decomposing a simple single-hop query just adds
latency, cost, and retrieval dilution. So a single cheap LLM call decides
*whether* to decompose and, if so, returns the sub-questions in one shot.
"""
from __future__ import annotations

from .llm import LLMClient, get_llm

_SYSTEM = (
    "You are a query analyzer for a retrieval system. Decide whether a question "
    "is multi-hop/comparative (needs several distinct pieces of evidence) or "
    "simple (one lookup answers it). Only decompose when genuinely needed."
)

_PROMPT = """Analyze this question and respond with a JSON object only.

Question: {query}

Rules:
- "is_multi_hop": true only if answering requires combining 2+ separate facts,
  comparing entities, or covering distinct aspects. Otherwise false.
- "sub_questions": if multi-hop, 2-4 standalone sub-questions, each independently
  retrievable (no pronouns referring across them). If not multi-hop, an empty list.

Respond exactly as:
{{"is_multi_hop": <bool>, "sub_questions": [<string>, ...]}}"""


class QueryDecomposer:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or get_llm()

    def decompose(self, query: str) -> list[str]:
        """Return sub-questions if the query is multi-hop, else [] (meaning: just
        retrieve for the original query). Fails safe to [] on any LLM/parse error."""
        try:
            data = self.llm.complete_json(
                _PROMPT.format(query=query), system=_SYSTEM, max_tokens=400
            )
        except Exception:
            return []
        if not data.get("is_multi_hop"):
            return []
        subs = [s.strip() for s in data.get("sub_questions", []) if isinstance(s, str)]
        subs = [s for s in subs if s]
        # Guard against the model echoing the original or producing a single sub-q.
        return subs if len(subs) >= 2 else []
