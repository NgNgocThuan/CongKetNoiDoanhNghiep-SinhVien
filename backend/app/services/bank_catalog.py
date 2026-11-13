"""Snapshot retrieved 2026-11-12 from https://api.vietqr.io/v2/banks."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def banks():
    return json.loads((Path(__file__).parents[1] / "data/vietqr_banks.json").read_text(encoding="utf-8"))
