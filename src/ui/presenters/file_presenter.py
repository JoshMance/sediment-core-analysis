"""
FilePresenter - connects FileBrowser view to AppController

Follows MVP pattern where Presenter:
- Handles View events -> calls AppController methods
- Handles Store events -> updates the View's state
"""
from __future__ import annotations

import os

from PySide6.QtCore import QObject

from src.ui.views.shell.file_browser import FileBrowser
from src.domain.store import Store
from src.application import AppController

class FilePresenter(QObject):
    def __init__(self, view: FileBrowser, store: Store, controller: AppController):
        super().__init__()
        self.view = view
        self.store = store
        self.controller = controller
        # Double-clicking a file means the user wants to select/open it
        self.view.fileDoubleClicked.connect(self._on_file_selected)

    # Presenter interprets a double-click as file selection,
    # checks the type and handles accordingly
    def _on_file_selected(self, file_path: str):
        _, ext = os.path.splitext(file_path.lower())
        if ext in (".png", ".jpg", ".jpeg"):
            self.controller.create_image_entity(file_path)
        elif ext == '.csv':
            print(f"Data file: {file_path}")
        else:
            print(f"Unknown file type: {file_path}")