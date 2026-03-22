from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                                QTreeView, QHeaderView, QFileSystemModel,
                                QLabel)
from PySide6.QtCore import Signal, QDir


class FileBrowser(QWidget):
    """File system navigation sidebar — persists for the lifetime of the shell."""
    
    # Signals - raw UI events only, no interpretation
    fileClicked = Signal(str)       # File path on single-click
    fileDoubleClicked = Signal(str) # File path on double-click

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = QFileSystemModel()
        self._model.setRootPath("")

        self._tree_view = QTreeView()
        self._tree_view.setModel(self._model)
        self._tree_view.setAnimated(True)
        self._tree_view.setIndentation(20)
        self._tree_view.setSortingEnabled(True)

        self._tree_view.setColumnHidden(1, True)
        self._tree_view.setColumnHidden(2, True)
        self._tree_view.setColumnHidden(3, True)

        header = self._tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._tree_view.clicked.connect(self._on_file_clicked)
        self._tree_view.doubleClicked.connect(self._on_file_double_clicked)

        self._tree_view.setRootIndex(self._model.index(QDir.homePath()))

        panel_header = QLabel("Files")
        panel_header.setObjectName("panelHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panel_header)
        layout.addWidget(self._tree_view)

    def _on_file_clicked(self, index):
        if not self._model.isDir(index):
            self.fileClicked.emit(self._model.filePath(index))

    def _on_file_double_clicked(self, index):
        if self._model.isDir(index):
            self._tree_view.setRootIndex(index)
        else:
            self.fileDoubleClicked.emit(self._model.filePath(index))

    def navigate_to(self, path: str):
        """Navigate to a specific path (public method)."""
        self._navigate_to_path(path)

    def get_selected_file_path(self) -> str | None:
        """Get the path of the currently selected file/folder."""
        indexes = self._tree_view.selectedIndexes()
        if indexes:
            return self._model.filePath(indexes[0])
        return None
