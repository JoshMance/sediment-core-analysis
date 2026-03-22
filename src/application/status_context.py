"""StatusContext — application-layer channel for view context updates.

Owned by AppController. Any presenter that holds the controller can post
context strings (e.g. row/column position, cursor coordinates) via
AppController.set_view_context(). StatusBarPresenter subscribes to
contextChanged to render the right side of the status bar.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class StatusContext(QObject):
    """Thin signal relay. Carries up to N display strings to the status bar."""

    contextChanged = Signal(list)  # list[str]

    def set(self, parts: list[str]) -> None:
        self.contextChanged.emit(parts)
