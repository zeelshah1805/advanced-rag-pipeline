"""Answer generation + citation contract + post-hoc validation.

The prompt forces the model to cite every claim with the chunk's `[chunk_id]`.
After generation we validate every cited id against the set we actually
retrieved — hallucinated cites are stripped and counted, and the surviving
fraction becomes the `citation_validity` metric. That check is the thing that
makes the answers trustworthy (and is a talking point in itself).
"""
from __future__ import annotations

import re

from .config import CONFIG
from .llm import LLMClient, get_llm
from .schema import Answer, Retrieved

_SYSTEM = (
    "You are a precise question-answering assistant. Answer ONLY from the provided "
    "context. If the context does not contain the answer, say you don't have enough "
    "information. Never use outside knowledge."
)

_PROMPT = """Answer the question using only the context below.

CITATION RULES (mandatory):
- After every sentence or claim, cite the source chunk(s) it came from using
  their exact id in square brackets, e.g. [{example_id}].
- You may cite multiple ids like [{example_id}][...]. Cite only ids that appear
  in the context. Do not invent ids.
- If the context is insufficient, say so plainly (no citation needed for that).

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with inline [chunk_id] citations):"""

_CITE_RE = re.compile(r"\[([^\[\]]+?)\]")


def _format_context(retrieved: list[Retrieved]) -> str:
    blocks = []
    for r in retrieved:
        c = r.chunk
        loc = f"{c.source}" + (f", p.{c.page}" if c.page is not None else "")
        blocks.append(f"[{c.chunk_id}] (source: {loc})\n{c.text}")
    return "\n\n".join(blocks)


class AnswerGenerator:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or get_llm()

    def generate(self, query: str, retrieved: list[Retrieved]) -> Answer:
        if not retrieved:
            return Answer(
                text="I don't have enough information in the corpus to answer that.",
                retrieved=[],
            )
        example_id = retrieved[0].chunk_id
        prompt = _PROMPT.format(
            context=_format_context(retrieved),
            query=query,
            example_id=example_id,
        )
        text = self.llm.complete(prompt, system=_SYSTEM, max_tokens=1024)
        return self._validate_citations(text, retrieved)

    # --- citation validation ----------------------------------------------
    def _validate_citations(self, text: str, retrieved: list[Retrieved]) -> Answer:
        retrieved_ids = {r.chunk_id for r in retrieved}
        cited_raw = _CITE_RE.findall(text)
        # a bracket may hold several ids glued together: "[a][b]" already split,
        # but also tolerate "[a, b]" or "[a b]"
        cited_ids: list[str] = []
        for token in cited_raw:
            for piece in re.split(r"[,\s]+", token.strip()):
                if piece:
                    cited_ids.append(piece)

        valid, invalid = [], []
        for cid in cited_ids:
            (valid if cid in retrieved_ids else invalid).append(cid)

        # strip hallucinated citations from the rendered text
        clean_text = text
        for bad in set(invalid):
            clean_text = clean_text.replace(f"[{bad}]", "")
        clean_text = re.sub(r"[ \t]{2,}", " ", clean_text).strip()

        valid_set = set(valid)
        cited = [r for r in retrieved if r.chunk_id in valid_set]
        total_cites = len(cited_ids)
        validity = (len(valid) / total_cites) if total_cites else 1.0

        return Answer(
            text=clean_text,
            cited=cited,
            retrieved=retrieved,
            invalid_citations=sorted(set(invalid)),
            citation_validity=round(validity, 4),
            meta={"num_citations": total_cites, "context_size": len(retrieved)},
        )
