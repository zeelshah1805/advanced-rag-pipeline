"""Load the held-out evaluation set."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

EVAL_PATH = Path(__file__).resolve().parent / "eval_set.jsonl"


@dataclass
class EvalItem:
    id: str
    question: str
    ground_truth: str
    gold_docs: list[str]
    category: str


def load_eval_set(path: Path | None = None) -> list[EvalItem]:
    path = path or EVAL_PATH
    items: list[EvalItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        items.append(
            EvalItem(
                id=d["id"],
                question=d["question"],
                ground_truth=d["ground_truth"],
                gold_docs=d.get("gold_docs", []),
                category=d.get("category", "uncategorized"),
            )
        )
    return items
