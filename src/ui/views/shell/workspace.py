"""WorkspaceView — shell view that hosts runtime panels as closable tabs."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget


class WorkspaceView(QWidget):
    """Always-present center shell component that displays open panels.

    Hosts one tab per open entity. Closing a tab emits ``tabClosed``
    with the entity_id so the WorkspacePresenter can clean up.
    """

    tabClosed = Signal(str)  # entity_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setDocumentMode(True)
        self._tabs.tabCloseRequested.connect(self._on_tab_close_requested)

        # entity_id → panel widget (stable reference independent of tab index)
        self._entity_widgets: dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    # ── Public API ────────────────────────────────────────────

    def add_tab(self, widget: QWidget, title: str, entity_id: str) -> None:
        """Add a panel tab and make it active."""
        self._entity_widgets[entity_id] = widget
        index = self._tabs.addTab(widget, title)
        self._tabs.setCurrentIndex(index)

    def remove_tab(self, entity_id: str) -> None:
        """Remove the tab for this entity (called programmatically)."""
        widget = self._entity_widgets.pop(entity_id, None)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.removeTab(index)

    def focus_tab(self, entity_id: str) -> None:
        """Bring the tab for this entity to the front."""
        widget = self._entity_widgets.get(entity_id)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.setCurrentIndex(index)

    # ── Internal slots ────────────────────────────────────────

    def _on_tab_close_requested(self, index: int) -> None:
        """User clicked the tab close button — remove tab and notify."""
        widget = self._tabs.widget(index)
        entity_id = next(
            (eid for eid, w in self._entity_widgets.items() if w is widget),
            None,
        )
        if entity_id is None:
            return
        self._tabs.removeTab(index)
        self._entity_widgets.pop(entity_id)
        self.tabClosed.emit(entity_id)
