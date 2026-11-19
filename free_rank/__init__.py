"""Formula-only ranking of the free models on OpenCode Zen and Go, Kilo and OpenRouter.

Run ``python3 -m free_rank --help``. Every constant lives in ``config.json``; the code holds
no model names, versions or route ids (``tests/test_free_rank.py`` enforces this).
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parent
CONFIG = PACKAGE / "config.json"


@functools.lru_cache(maxsize=None)
def _load(path: str) -> str:
    return Path(path).read_text()


def load_config(path: Path | None = None) -> dict:
    return json.loads(_load(str(path or CONFIG)))
