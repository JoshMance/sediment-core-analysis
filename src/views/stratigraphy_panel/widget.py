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
        
        # Canvas
        self.canvas = StratigraphyCanvas(self)
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
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
