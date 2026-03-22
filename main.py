"""The app root - creates the three layers and wires them together."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout

# Domain layer
from src.domain.store import Store

# Application layer
from src.application import AppController
from src.application.workspace_state import WorkspaceState

# UI layer - views
from src.ui.views.shell.file_browser import FileBrowser
from src.ui.views.shell.variables_list import VariablesList
from src.ui.views.shell.preview import PreviewPanel
from src.ui.views.shell.ribbon.ribbon import Ribbon
from src.ui.views.shell.workspace import WorkspaceView
from src.ui.views.shell.status_bar import StatusBar

# UI layer - presenters
from src.ui.presenters.file_presenter import FilePresenter
from src.ui.presenters.variables_presenter import VariablesPresenter
from src.ui.presenters.ribbon_presenter import RibbonPresenter
from src.ui.presenters.workspace_presenter import WorkspacePresenter
from src.ui.presenters.status_bar_presenter import StatusBarPresenter
from src.ui.resources.theme import apply_theme


def main() -> None:
    dev_mode = "--dev" in sys.argv
    app = QApplication(sys.argv)
    dark = True if "--dark" in sys.argv else (False if "--light" in sys.argv else None)
    apply_theme(app, dark=dark)

    from PySide6.QtCore import Qt
    _logo_dir = Path(__file__).parent / "src" / "ui" / "resources" / "logo"
    _os_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    _logo = _logo_dir / ("logo_light.svg" if _os_dark else "logo_dark.svg")
    app.setWindowIcon(QIcon(str(_logo)))

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
    workspace_state = WorkspaceState(store=store)
    controller = AppController(store, workspace_state=workspace_state, component_watcher=watch)

    # -- UI - views -----------------------------------------------
    ribbon = Ribbon()
    watch("Ribbon", ribbon)
    file_browser = FileBrowser()
    watch("FileBrowser", file_browser)
    variables_list = VariablesList()
    watch("VariablesList", variables_list)
    preview_panel = PreviewPanel()
    workspace_view = WorkspaceView()
    watch("WorkspaceView", workspace_view)

    # -- UI - presenters ------------------------------------------
    ribbon_presenter = RibbonPresenter(ribbon, controller)
    file_presenter = FilePresenter(file_browser, store, controller)
    variables_presenter = VariablesPresenter(variables_list, preview_panel, store, controller)
    workspace_presenter = WorkspacePresenter(workspace_view, workspace_state, store, controller)

    if dev_log:
        dev_log.show()

    # -- Layout ---------------------------------------------------
    right_column = QWidget()
    right_layout = QVBoxLayout(right_column)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(4)
    right_layout.addWidget(variables_list, 1)
    right_layout.addWidget(preview_panel)

    bottom_row = QWidget()
    bottom_layout = QHBoxLayout(bottom_row)
    bottom_layout.setContentsMargins(4, 4, 4, 4)
    bottom_layout.setSpacing(4)
    bottom_layout.addWidget(file_browser, 1)
    bottom_layout.addWidget(workspace_view, 3)
    bottom_layout.addWidget(right_column, 1)

    central = QWidget()
    central_layout = QVBoxLayout(central)
    central_layout.setContentsMargins(0, 0, 0, 0)
    central_layout.setSpacing(0)
    central_layout.addWidget(ribbon)
    central_layout.addWidget(bottom_row, 1)

    # -- Window ---------------------------------------------------
    window = QMainWindow()
    window.setWindowTitle("Sedivis")
    window.setCentralWidget(central)
    window.resize(1200, 800)
    status_bar = StatusBar()
    window.setStatusBar(status_bar)
    status_bar_presenter = StatusBarPresenter(status_bar, store, controller.status_context)
    status_bar.show_message("Ready")
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
