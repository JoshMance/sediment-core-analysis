"""Munsell hue data loader.

Reads science/data/munsell_hues.json — a flat list of hue objects.
Each hue has a ``cells`` 2D array of notation strings (or null for empty cells).
The code here knows nothing about values, chromas, or chips.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

_HUES_FILE = pathlib.Path(__file__).parent.parent / "data" / "munsell_hues.json"


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict]:
    raw: list[dict] = json.loads(_HUES_FILE.read_text(encoding="utf-8"))
    return {h["hue"]: h for h in raw}


def available_hues() -> list[str]:
    """Return the list of available hue names (e.g. ['5R', '10R', ...])."""
    return list(_registry().keys())


def get_hue(hue: str) -> dict:
    """Return the hue dict (keys: 'hue', 'cells') or raise KeyError."""
    try:
        return _registry()[hue]
    except KeyError:
        raise KeyError(f"Munsell hue {hue!r} not found. Available: {available_hues()}") from None
