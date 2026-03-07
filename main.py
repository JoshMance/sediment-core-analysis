"""The app root - creates the three layers and wires them together."""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout

# Domain layer
from src.domain.store import Store

# Application layer
from src.application import AppController

# UI layer - views
from src.ui.views.panels.file_panel import FilePanel
from src.ui.views.panels.workspace_panel import WorkspacePanel
from src.ui.views.shell.ribbon import Ribbon

# UI layer - presenters
from src.ui.presenters.file_presenter import FilePresenter
from src.ui.presenters.workspace_presenter import WorkspacePresenter
from src.ui.presenters.ribbon_presenter import RibbonPresenter
from src.ui.resources.theme import apply_theme


def main() -> None:
    dev_mode = "--dev" in sys.argv
    app = QApplication(sys.argv)
    dark = True if "--dark" in sys.argv else (False if "--light" in sys.argv else None)
    apply_theme(app, dark=dark)

    # -- Dev log (optional) ---------------------------------------
    dev_log = None
    if dev_mode:
        from tests.helpers.dev_log import DevLog
        dev_log = DevLog()

    def watch(name: str, obj: object) -> None:
        if dev_log:
            dev_log.watch(name, obj)

    # -- Domain ---------------------------------------------------
    store = Store()
    watch("Store", store)

    # -- Application ----------------------------------------------
    controller = AppController(store, component_watcher=watch)

    # -- UI - views -----------------------------------------------
    ribbon = Ribbon()
    watch("Ribbon", ribbon)
    file_panel = FilePanel()
    watch("FilePanel", file_panel)
    workspace_panel = WorkspacePanel()
    watch("WorkspacePanel", workspace_panel)

    # -- UI - presenters ------------------------------------------
    ribbon_presenter = RibbonPresenter(ribbon, controller)
    file_presenter = FilePresenter(file_panel, store, controller)
    workspace_presenter = WorkspacePresenter(workspace_panel, store, controller)

    if dev_log:
        dev_log.show()

    # -- Layout ---------------------------------------------------
    bottom_row = QWidget()
    bottom_layout = QHBoxLayout(bottom_row)
    bottom_layout.setContentsMargins(0, 0, 0, 0)
    bottom_layout.addWidget(file_panel, 1)
    bottom_layout.addWidget(QWidget(), 3)
    bottom_layout.addWidget(workspace_panel, 1)

    central = QWidget()
    central_layout = QVBoxLayout(central)
    central_layout.setContentsMargins(0, 0, 0, 0)
    central_layout.addWidget(ribbon)
    central_layout.addWidget(bottom_row, 1)

    # -- Window ---------------------------------------------------
    window = QMainWindow()
    window.setWindowTitle("Sediment Core Analysis")
    window.setCentralWidget(central)
    window.resize(1200, 800)
    window.statusBar().showMessage("Ready")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
