from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QPushButton
from PySide6.QtCore import QSize
from .canvas import StratigraphyCanvas
from .signals import StratigraphySignals

class StratigraphyPanel(QWidget):
    """Main widget for stratigraphy visualization and interaction."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Signals
        self.signals = StratigraphySignals()
        
        # Canvas (private)
        self._canvas = StratigraphyCanvas(self)
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self._canvas)
        
    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with controls."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setFixedSize(70, 32)
        self.add_btn.setCheckable(True)
        self.add_btn.clicked.connect(self._on_add_clicked)
        toolbar.addWidget(self.add_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFixedSize(70, 32)
        self.delete_btn.setCheckable(True)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        toolbar.addWidget(self.delete_btn)
        
        return toolbar
    
    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        if self.add_btn.isChecked():
            self.delete_btn.setChecked(False)
            self._canvas.set_interaction_mode('add')
        else:
            self._canvas.set_interaction_mode(None)
    
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        if self.delete_btn.isChecked():
            self.add_btn.setChecked(False)
            self._canvas.set_interaction_mode('delete')
        else:
            self._canvas.set_interaction_mode(None)
    
    # Public API - forward to canvas
    
    def add_column(self, column) -> None:
        """Add a column to the stratigraphy display."""
        self._canvas.add_column(column)
    
    def set_columns(self, columns: list) -> None:
        """Set all columns at once."""
        self._canvas.set_columns(columns)
    
    def set_title(self, title: str) -> None:
        """Set the stratigraphy title."""
        self._canvas.set_title(title)
    
    def set_depth_range(self, min_depth: float, max_depth: float) -> None:
        """Set the depth range for the display."""
        self._canvas.depth_range = (min_depth, max_depth)
        self._canvas.update()
    
    def add_row_divider(self, depth: float) -> None:
        """Add a horizontal divider at the specified depth."""
        self._canvas.add_row_divider(depth)
