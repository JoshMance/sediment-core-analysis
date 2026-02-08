from PySide6.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QPushButton, 
                                QTreeView, QHeaderView, QFileDialog)
from PySide6.QtCore import QDir, QSize
from PySide6.QtWidgets import QFileSystemModel
from .signals import FilePanelSignals


class FilePanel(QWidget):
    """Main widget providing a file system tree view for navigation."""

    def __init__(self, parent: QWidget | None = None, root_path: str | None = None) -> None:
        super().__init__(parent)

        # Signals
        self.signals = FilePanelSignals()

        # File system model
        self._model = QFileSystemModel(self)
        self._root_path = root_path or QDir.currentPath()
        self._model.setRootPath(self._root_path)

        # Tree view
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._model)
        self._tree_view.setRootIndex(self._model.index(self._root_path))
        self._tree_view.setAnimated(True)
        self._tree_view.setIndentation(20)
        self._tree_view.setSortingEnabled(True)

        # Hide extra columns (size, type, date modified) for a cleaner look
        header = self._tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, self._model.columnCount()):
            self._tree_view.setColumnHidden(col, True)

        # Connect signals
        self._tree_view.clicked.connect(self._on_item_clicked)
        self._tree_view.doubleClicked.connect(self._on_item_double_clicked)

        # Toolbar
        self.toolbar = self._create_toolbar()

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self._tree_view)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with file navigation controls."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Home button
        self.home_btn = QPushButton("Home")
        self.home_btn.setToolTip("Go to home directory")
        self.home_btn.clicked.connect(self._on_home_clicked)
        toolbar.addWidget(self.home_btn)

        # Spacer to push browse button to right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, 
                             spacer.sizePolicy().verticalPolicy().Preferred)
        toolbar.addWidget(spacer)

        # Browse button (three dots)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setToolTip("Browse for folder")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        toolbar.addWidget(self.browse_btn)

        return toolbar

    def _on_item_clicked(self, index) -> None:
        """Handle single click on tree item."""
        path = self._model.filePath(index)
        if self._model.isDir(index):
            self.signals.directoryChanged.emit(path)
        else:
            self.signals.fileSelected.emit(path)

    def _on_item_double_clicked(self, index) -> None:
        """Handle double click on tree item."""
        path = self._model.filePath(index)
        if not self._model.isDir(index):
            self.signals.fileSelected.emit(path)

    def _on_home_clicked(self) -> None:
        """Navigate to home directory."""
        home_path = QDir.homePath()
        self.set_root_path(home_path)

    def _on_browse_clicked(self) -> None:
        """Open OS folder picker and navigate to selected folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self._root_path,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.set_root_path(folder)

    def set_root_path(self, path: str) -> None:
        """Set the root path for the file tree."""
        self._root_path = path
        self._model.setRootPath(path)
        self._tree_view.setRootIndex(self._model.index(path))
        self.signals.directoryChanged.emit(path)

    def get_selected_path(self) -> str | None:
        """Get the currently selected file/folder path."""
        indexes = self._tree_view.selectedIndexes()
        if indexes:
            return self._model.filePath(indexes[0])
        return None
