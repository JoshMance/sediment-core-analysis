"""RibbonContext — application-layer channel for ribbon tab navigation.

Owned by AppController. Any presenter that holds the controller can request
a ribbon tab change via AppController.set_ribbon_tab(). RibbonPresenter
subscribes to tabRequested to switch the active tab.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class RibbonContext(QObject):
    """Thin signal relay. Requests a ribbon tab change by name."""

    tabRequested = Signal(str)  # tab_name

    def set_tab(self, tab_name: str) -> None:
        self.tabRequested.emit(tab_name)
