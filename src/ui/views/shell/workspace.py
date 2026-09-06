"""WorkspaceView — shell view that hosts runtime panels as closable tabs."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.views.shell.variables_list import ENTITY_MIME_TYPE

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
        primary.setStyleSheet("font-size: 16px; font-weight: 600;")

        secondary = QLabel("Open an image to get started")
        secondary.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        secondary.setStyleSheet("font-size: 12px;")

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
        self.setObjectName("workspacePlaceholder")


class WorkspaceView(QWidget):
    """Always-present center shell component that displays open panels.

    Hosts one tab per open panel. Closing a tab emits ``tabClosed``
    with the panel_id so the WorkspacePresenter can clean up.
    """

    tabClosed = Signal(str)     # panel_id
    tabChanged = Signal(str)     # panel_id of newly active tab ("" when none)
    entityDropped = Signal(str)  # entity_id — user dropped an entity onto workspace

    _PAGE_EMPTY = 0
    _PAGE_TABS = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setDocumentMode(True)
        self._tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self._tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tabs.currentChanged.connect(self._on_current_changed)

        # panel_id → panel widget (stable reference independent of tab index)
        self._panel_widgets: dict[str, QWidget] = {}

        self._stack = QStackedWidget()
        self._stack.setObjectName("panelContent")
        self._stack.addWidget(_EmptyWorkspacePlaceholder())
        self._stack.addWidget(self._tabs)
        self._stack.setCurrentIndex(self._PAGE_EMPTY)

        self._header = QLabel("Workspace")
        self._header.setObjectName("panelHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._stack)

    # ── Public API ────────────────────────────────────────────

    def add_tab(self, widget: QWidget, title: str, panel_id: str) -> None:
        """Add a panel tab and make it active."""
        self._panel_widgets[panel_id] = widget
        index = self._tabs.addTab(widget, title)
        self._tabs.setCurrentIndex(index)
        self._stack.setCurrentIndex(self._PAGE_TABS)
        self._header.setVisible(False)

    def remove_tab(self, panel_id: str) -> None:
        """Remove the tab for this panel (called programmatically)."""
        widget = self._panel_widgets.pop(panel_id, None)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.removeTab(index)
        if not self._panel_widgets:
            self._stack.setCurrentIndex(self._PAGE_EMPTY)
            self._header.setVisible(True)

    def focus_tab(self, panel_id: str) -> None:
        """Bring the tab for this panel to the front."""
        widget = self._panel_widgets.get(panel_id)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.setCurrentIndex(index)

    def rename_tab(self, panel_id: str, new_name: str) -> None:
        """Update the tab title for the given panel."""
        widget = self._panel_widgets.get(panel_id)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index != -1:
            self._tabs.setTabText(index, new_name)

    # ── Internal slots ────────────────────────────────────────

    def _on_current_changed(self, index: int) -> None:
        """QTabWidget current tab changed — emit the panel_id."""
        if index < 0:
            self.tabChanged.emit("")
            return
        widget = self._tabs.widget(index)
        panel_id = next(
            (pid for pid, w in self._panel_widgets.items() if w is widget),
            "",
        )
        self.tabChanged.emit(panel_id)

    def _on_tab_close_requested(self, index: int) -> None:
        """User clicked the tab close button — remove tab and notify."""
        widget = self._tabs.widget(index)
        panel_id = next(
            (pid for pid, w in self._panel_widgets.items() if w is widget),
            None,
        )
        if panel_id is None:
            return
        self._tabs.removeTab(index)
        self._panel_widgets.pop(panel_id)
        if not self._panel_widgets:
            self._stack.setCurrentIndex(self._PAGE_EMPTY)
            self._header.setVisible(True)
        self.tabClosed.emit(panel_id)

    # ── Drag and drop ─────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasFormat(ENTITY_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        data = event.mimeData().data(ENTITY_MIME_TYPE)
        if data.isEmpty():
            return
        entity_id = bytes(data).decode("utf-8")
        event.acceptProposedAction()
        self.entityDropped.emit(entity_id)
