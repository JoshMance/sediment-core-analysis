"""WorkspaceView — shell view that hosts runtime panels as closable tabs."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

_LOGO_GREY = Path(__file__).parent.parent.parent / "resources" / "logo" / "logo_grey.svg"


class _EmptyWorkspacePlaceholder(QWidget):
    """Shown in the workspace area when no panels are open."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        logo = QSvgWidget(str(_LOGO_GREY))
        logo.setFixedSize(80, 100)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()

        primary = QLabel("Welcome to Sedivis")
        primary.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        primary.setStyleSheet("color: #333333; font-size: 16px; font-weight: 600;")

        secondary = QLabel("Open an image to get started")
        secondary.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        secondary.setStyleSheet("color: #888888; font-size: 12px;")

        inner = QVBoxLayout()
        inner.setSpacing(0)
        inner.addLayout(logo_row)
        inner.addSpacing(18)
        inner.addWidget(primary)
        inner.addSpacing(6)
        inner.addWidget(secondary)

        outer = QVBoxLayout(self)
        outer.addStretch()
        outer.addLayout(inner)
        outer.addStretch()


class WorkspaceView(QWidget):
    """Always-present center shell component that displays open panels.

    Hosts one tab per open entity. Closing a tab emits ``tabClosed``
    with the entity_id so the WorkspacePresenter can clean up.
    """

    tabClosed = Signal(str)  # entity_id

    _PAGE_EMPTY = 0
    _PAGE_TABS = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setDocumentMode(True)
        self._tabs.tabCloseRequested.connect(self._on_tab_close_requested)

        # entity_id → panel widget (stable reference independent of tab index)
        self._entity_widgets: dict[str, QWidget] = {}

        self._stack = QStackedWidget()
        self._stack.addWidget(_EmptyWorkspacePlaceholder())
        self._stack.addWidget(self._tabs)
        self._stack.setCurrentIndex(self._PAGE_EMPTY)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    # ── Public API ────────────────────────────────────────────

    def add_tab(self, widget: QWidget, title: str, entity_id: str) -> None:
        """Add a panel tab and make it active."""
        self._entity_widgets[entity_id] = widget
        index = self._tabs.addTab(widget, title)
        self._tabs.setCurrentIndex(index)
        self._stack.setCurrentIndex(self._PAGE_TABS)

    def remove_tab(self, entity_id: str) -> None:
        """Remove the tab for this entity (called programmatically)."""
        widget = self._entity_widgets.pop(entity_id, None)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.removeTab(index)
        if not self._entity_widgets:
            self._stack.setCurrentIndex(self._PAGE_EMPTY)

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
        if not self._entity_widgets:
            self._stack.setCurrentIndex(self._PAGE_EMPTY)
        self.tabClosed.emit(entity_id)
