"""
FilePresenter - connects FilePanel view to Store/Controller

Follows MVP pattern where Presenter:
- Handles View events -> calls Controller methods
- Handles Store events -> updates the View's state
"""
import os
from PySide6.QtCore import QObject
from src.views.panels.file_panel import FilePanel


class FilePresenter(QObject):
    def __init__(self, view: FilePanel):
        super().__init__()
        self.view = view
        # Double-clicking a file means the user wants to select/open it
        self.view.fileDoubleClicked.connect(self._on_file_selected)

    # Presenter interprets a double-click as file selection,
    # checks the type and handles accordingly
    def _on_file_selected(self, file_path: str):
        _, ext = os.path.splitext(file_path.lower())
        match ext:
            case '.jpg' | '.jpeg' | '.png':
                print(f"Image file: {file_path}")

            case '.csv':
                print(f"Data file: {file_path}")

            case _:
                print(f"Unknown file type: {file_path}")