from PySide6.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QPushButton, 
                                QTreeView, QHeaderView, QFileSystemModel, QFileDialog)
from PySide6.QtCore import QSize, Signal, QDir


class FileBrowser(QWidget):
    """File system navigation sidebar — persists for the lifetime of the shell."""
    
    # Signals - raw UI events only, no interpretation
    fileClicked = Signal(str)      # File path on single-click
    fileDoubleClicked = Signal(str) # File path on double-click
    pathChanged = Signal(str)       # Current directory path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Create file system model
        self._model = QFileSystemModel()
        self._model.setRootPath("")  # Can access entire file system
        
        # Tree view with model
        self._tree_view = QTreeView()
        self._tree_view.setModel(self._model)
        self._tree_view.setAnimated(True)
        self._tree_view.setIndentation(20)
        self._tree_view.setSortingEnabled(True)

        # Hide extra columns (Size, Type, Date Modified)
        self._tree_view.setColumnHidden(1, True)  # Size
        self._tree_view.setColumnHidden(2, True)  # Type
        self._tree_view.setColumnHidden(3, True)  # Date Modified

        # Configure header
        header = self._tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Connect view events
        self._tree_view.clicked.connect(self._on_file_clicked)
        self._tree_view.doubleClicked.connect(self._on_file_double_clicked)

        # Start in user's home directory
        self._current_path = QDir.homePath()
        self._tree_view.setRootIndex(self._model.index(self._current_path))

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
        self.home_btn.clicked.connect(self._go_home)
        toolbar.addWidget(self.home_btn)

        # Spacer to push browse button to right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, 
                             spacer.sizePolicy().verticalPolicy().Preferred)
        toolbar.addWidget(spacer)

        # Browse button
        self.browse_btn = QPushButton("...")
        self.browse_btn.setToolTip("Browse for folder")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self._browse_for_folder)
        toolbar.addWidget(self.browse_btn)

        return toolbar
    
    def _on_file_clicked(self, index):
        """Handle single-click - emit file path."""
        if not self._model.isDir(index):
            self.fileClicked.emit(self._model.filePath(index))
    
    def _on_file_double_clicked(self, index):
        """Handle double-click - navigate into dirs, emit file path for files."""
        if self._model.isDir(index):
            self._navigate_to_index(index)
        else:
            self.fileDoubleClicked.emit(self._model.filePath(index))
    
    def _go_home(self):
        """Navigate to user's home directory."""
        self._navigate_to_path(QDir.homePath())
    
    def _browse_for_folder(self):
        """Open dialog to browse for a folder."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder", 
            self._current_path
        )
        if folder:
            self._navigate_to_path(folder)
    
    def _navigate_to_path(self, path: str):
        """Navigate to a specific path."""
        index = self._model.index(path)
        if index.isValid():
            self._navigate_to_index(index)
    
    def _navigate_to_index(self, index):
        """Navigate to a specific model index."""
        self._tree_view.setRootIndex(index)
        self._current_path = self._model.filePath(index)
        self.pathChanged.emit(self._current_path)
    
    # Public interface for external control (if needed)
    
    def get_current_path(self) -> str:
        """Get the current directory path."""
        return self._current_path
    
    def navigate_to(self, path: str):
        """Navigate to a specific path (public method)."""
        self._navigate_to_path(path)

    def get_selected_file_path(self) -> str | None:
        """Get the path of the currently selected file/folder."""
        indexes = self._tree_view.selectedIndexes()
        if indexes:
            return self._model.filePath(indexes[0])
        return None
