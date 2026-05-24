"""Munsell reference data — registry and typed accessors.

This module is the single interface between all Munsell data and the rest of
the codebase. Each JSON file in ``science/data/`` describes one physical
book and is loaded lazily on first access.

Typical usage::

    from science.lib.munsell import available_books, get_book

    print(available_books())                    # ['Munsell Nearly Neutrals', ...]
    book = get_book("Munsell Nearly Neutrals")
    for page in book.pages:
        for row in page.values:
            for chip in row.chromas:
                print(chip.notation, chip.chroma)
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data"


# ── Typed data model ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MunsellChip:
    """A single colour chip: its full Munsell notation and chroma step."""
    notation: str   # e.g. "5R 9/2"
    chroma: float


@dataclass(frozen=True)
class MunsellValueRow:
    """All chips at a given value level within one page."""
    value: float
    chromas: tuple[MunsellChip, ...]

    def chip(self, chroma: float) -> MunsellChip | None:
        return next((c for c in self.chromas if c.chroma == chroma), None)


@dataclass(frozen=True)
class MunsellPage:
    """One page in a Munsell book — identified by hue (e.g. '5R').

    Each page contains multiple value rows, each with a set of chroma chips.
    """
    hue: str
    values: tuple[MunsellValueRow, ...]

    def row(self, value: float) -> MunsellValueRow | None:
        return next((v for v in self.values if v.value == value), None)

    def chip(self, notation: str) -> MunsellChip | None:
        for row in self.values:
            for c in row.chromas:
                if c.notation == notation:
                    return c
        return None


@dataclass(frozen=True)
class MunsellBook:
    """One physical Munsell book, containing pages keyed by hue."""
    name: str
    pages: tuple[MunsellPage, ...]

    def page(self, hue: str) -> MunsellPage | None:
        """Return the page for the given hue (e.g. ``'5R'``), or ``None``."""
        return next((p for p in self.pages if p.hue == hue), None)

    def chip(self, notation: str) -> MunsellChip | None:
        """Look up any chip by its full notation string (e.g. ``'5R 9/2'``)."""
        for page in self.pages:
            result = page.chip(notation)
            if result is not None:
                return result
        return None


# ── Internal loader ───────────────────────────────────────────────────────────

def _load_book(path: pathlib.Path) -> MunsellBook:
    raw = json.loads(path.read_text(encoding="utf-8"))
    b = raw["book"]
    pages = tuple(
        MunsellPage(
            hue=h["hue"],
            values=tuple(
                MunsellValueRow(
                    value=v["value"],
                    chromas=tuple(
                        MunsellChip(notation=c["chip"], chroma=c["chroma"])
                        for c in v["chromas"]
                    ),
                )
                for v in h["values"]
            ),
        )
        for h in b["hues"]
    )
    return MunsellBook(name=b["name"], pages=pages)


@lru_cache(maxsize=1)
def _registry() -> dict[str, MunsellBook]:
    """Scan data/ and load every JSON book, keyed by book name."""
    books: dict[str, MunsellBook] = {}
    for path in sorted(_DATA_DIR.glob("*.json")):
        book = _load_book(path)
        books[book.name] = book
    return books


# ── Public API ────────────────────────────────────────────────────────────────

def available_books() -> list[str]:
    """Return the names of all available Munsell books."""
    return list(_registry().keys())


def get_book(name: str) -> MunsellBook:
    """Return the named book, raising ``KeyError`` if it isn't available."""
    try:
        return _registry()[name]
    except KeyError:
        raise KeyError(
            f"Munsell book {name!r} not found. "
            f"Available: {available_books()}"
        ) from None
