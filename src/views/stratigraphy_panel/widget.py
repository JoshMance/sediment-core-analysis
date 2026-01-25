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
        
        # Placeholder button
        example_btn = QPushButton("Example")
        example_btn.setFixedSize(70, 32)
        toolbar.addWidget(example_btn)
        
        return toolbar
    
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
