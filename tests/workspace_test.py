"""
Manual test for Workspace feature — end-to-end visual verification

Tests the full flow:
  1. Load an image via FileBrowser → FilePresenter → AppController → Store
  2. Double-click the image in VariablesList → WorkspacePresenter opens ImagePanel tab
  3. Draw a selection on the ImagePanel → confirm → CoreEntity appears in VariablesList

All signals are logged to a LogWindow for inspection.

Run with: python -m tests.workspace_test
"""
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
)

from src.domain.store import Store
from src.application import AppController
from src.application.workspace_state import WorkspaceState
from src.ui.views.shell.file_browser import FileBrowser
from src.ui.views.shell.variables_list import VariablesList
from src.ui.views.shell.preview import PreviewPanel
from src.ui.views.shell.workspace import WorkspaceView
from src.ui.presenters.file_presenter import FilePresenter
from src.ui.presenters.variables_presenter import VariablesPresenter
from src.ui.presenters.workspace_presenter import WorkspacePresenter
from tests.helpers import LogWindow, SignalLogger


class WorkspaceTest(QWidget):
    """Full workspace test: FileBrowser + VariablesList + WorkspaceView wired together."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workspace Test — End-to-End")
        self.resize(1400, 800)

        self.log_window = LogWindow("Workspace Test Logs", 500, 700)
        self.log_window.show()
        self.log_window.move(1450, 100)

        # -- Domain ---------------------------------------------------
        self.store = Store()

        # -- Application ----------------------------------------------
        self.workspace_state = WorkspaceState()
        self.controller = AppController(
            self.store, workspace_state=self.workspace_state
        )

        # -- UI -------------------------------------------------------
        self.file_browser = FileBrowser()
        self.variables_list = VariablesList()
        self.preview = PreviewPanel()
        self.workspace_view = WorkspaceView()
        self._opened_panel_ids: set[str] = set()

        # -- Presenters -----------------------------------------------
        self.file_presenter = FilePresenter(
            self.file_browser, self.store, self.controller
        )
        self.variables_presenter = VariablesPresenter(
            self.variables_list, self.preview, self.store, self.controller
        )
        self.workspace_presenter = WorkspacePresenter(
            self.workspace_view, self.workspace_state, self.store, self.controller
        )

        # -- Signal logging -------------------------------------------
        store_logger = SignalLogger(self.log_window, "Store")
        store_logger.connect_signal(self.store.entityAdded, "entityAdded")
        store_logger.connect_signal(self.store.entityRemoved, "entityRemoved")

        ws_logger = SignalLogger(self.log_window, "WorkspaceState")
        ws_logger.connect_signal(self.workspace_state.panelAdded, "panelAdded")
        ws_logger.connect_signal(self.workspace_state.panelRemoved, "panelRemoved")
        ws_logger.connect_signal(self.workspace_state.panelFocusRequested, "panelFocusRequested")
        self.workspace_state.panelAdded.connect(self._assert_unique_panel_identity)
        self.workspace_state.panelRemoved.connect(self._on_panel_removed)

        vl_logger = SignalLogger(self.log_window, "VariablesList")
        vl_logger.connect_signal(self.variables_list.entityOpenRequested, "entityOpenRequested")
        vl_logger.connect_signal(self.variables_list.deleteRequested, "deleteRequested")

        wv_logger = SignalLogger(self.log_window, "WorkspaceView")
        wv_logger.connect_signal(self.workspace_view.tabClosed, "tabClosed")

        # -- Layout ---------------------------------------------------
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.addWidget(self.file_browser, 1)
        main_layout.addWidget(self.workspace_view, 3)
        right = QVBoxLayout()
        right.addWidget(self.variables_list, 2)
        right.addWidget(self.preview, 1)
        main_layout.addLayout(right, 1)

        self.log_window.add_log(
            "Ready. Load an image, double-click it in VariablesList to open in workspace."
        )
        self.log_window.add_log(
            "In the ImagePanel: click Select, draw a region, click ✓ to create a CoreEntity."
        )

    def _assert_unique_panel_identity(self, entry) -> None:
        """Assert each open entity maps to at most one open workspace tab."""
        assert entry.entity_id not in self._opened_panel_ids, (
            f"Duplicate tab opened for entity_id '{entry.entity_id}'."
        )
        self._opened_panel_ids.add(entry.entity_id)

    def _on_panel_removed(self, entity_id: str, _entity_type: str | None = None) -> None:
        self._opened_panel_ids.discard(entity_id)

    def closeEvent(self, event):
        self.log_window.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    test = WorkspaceTest()
    test.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
