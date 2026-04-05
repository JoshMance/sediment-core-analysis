"""RecentDirs — remembers the last-used directory per file category.

Owned by AppController. Presenters that open file dialogs call
``get(category)`` to obtain the starting directory and ``set(category, path)``
after a successful load/save so the next dialog opens in the same place.

Categories are plain strings — no enum, no registration. Any presenter can
introduce a new category simply by using a new key (e.g. ``"image"``,
``"data"``, ``"session"``, ``"map"``).
"""
from __future__ import annotations

from pathlib import Path


class RecentDirs:
    """Maps category strings to the last-used directory path."""

    def __init__(self) -> None:
        self._dirs: dict[str, Path] = {}

    def get(self, category: str) -> Path:
        """Return the last directory used for *category*, or the user home."""
        return self._dirs.get(category, Path.home())

    def set(self, category: str, directory: Path) -> None:
        """Record *directory* as the last-used path for *category*."""
        self._dirs[category] = directory

    def clear(self) -> None:
        """Reset all remembered directories (e.g. on New Session)."""
        self._dirs.clear()
