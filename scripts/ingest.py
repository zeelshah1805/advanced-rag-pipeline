"""CLI: build the indexes.

  python -m scripts.ingest                 # ingest data/corpus, else the sample
  python -m scripts.ingest path/to/docs    # ingest specific files/dirs
"""
from __future__ import annotations

import sys
from pathlib import Path

from rag.ingest import ingest


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]] or None
    ingest(paths)


if __name__ == "__main__":
    main()
