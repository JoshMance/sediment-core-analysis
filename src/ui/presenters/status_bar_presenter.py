"""StatusBarPresenter — drives both sides of the status bar.

Left side: Store signals (entity added/removed/updated/reset).
Right side: StatusContext.contextChanged (view-local state from panel presenters).
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QTimer

from src.ui.views.shell.status_bar import StatusBar
from src.domain.store import Store
from src.application.status_context import StatusContext

_REVERT_MS = 5_000


class StatusBarPresenter(QObject):
    def __init__(
        self,
        status_bar: StatusBar,
        store: Store,
        status_context: StatusContext,
    ) -> None:
        super().__init__()
        self._bar = status_bar

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_REVERT_MS)
        self._timer.timeout.connect(self._revert)

        # Left side — Store events
        store.entityAdded.connect(self._on_added)
        store.entityRemoved.connect(self._on_removed)
        store.entityUpdated.connect(self._on_updated)
        store.storeReset.connect(self._on_reset)

        # Right side — view context from panel presenters
        status_context.contextChanged.connect(self._on_context)

    def _show(self, message: str) -> None:
        self._bar.show_message(message)
        self._timer.start()

    def _revert(self) -> None:
        self._bar.show_message("Ready")

    def _on_added(self, _id: str, entity_type: str) -> None:
        self._show(f"{entity_type} added")

    def _on_removed(self, _id: str, entity_type: str) -> None:
        self._show(f"{entity_type} removed")

    def _on_updated(self, _id: str, entity_type: str) -> None:
        self._show(f"{entity_type} updated")

    def _on_reset(self) -> None:
        self._show("Session cleared")

    def _on_context(self, parts: list[str]) -> None:
        self._bar.show_context(parts)
