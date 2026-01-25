from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, QScrollBar
from PySide6.QtCore import QSize
from .canvas import StratigraphyCanvas

class StratigraphyPanel(QWidget):
    """Main widget for stratigraphy visualization and interaction."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Canvas (private)
        self._canvas = StratigraphyCanvas(self)
        
        # Scrollbar
        self._scrollbar = QScrollBar()
        self._scrollbar.setMinimum(0)
        self._scrollbar.setMaximum(0)
        self._scrollbar.valueChanged.connect(self._on_scrollbar_changed)
        
        # Connect canvas to update scrollbar
        self._canvas.scroll_changed = self._update_scrollbar
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        
        # Layout: toolbar at top, then canvas + scrollbar in horizontal layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        
        # Horizontal layout for canvas and scrollbar
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._canvas)
        content_layout.addWidget(self._scrollbar)
        layout.addLayout(content_layout)
        
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
    
    def _on_scrollbar_changed(self, value: int) -> None:
        """Handle scrollbar value changes."""
        self._canvas.set_scroll_offset(float(value))
    
    def _update_scrollbar(self, offset: float, max_offset: float, page_size: float) -> None:
        """Update scrollbar range and position based on canvas state."""
        # Block signals to prevent circular updates
        self._scrollbar.blockSignals(True)
        
        # Always update range - Qt will hide/show thumb automatically based on range vs page_step
        self._scrollbar.setMinimum(0)
        self._scrollbar.setMaximum(max(0, int(max_offset)))
        self._scrollbar.setPageStep(max(1, int(page_size)))
        self._scrollbar.setSingleStep(max(1, int(page_size / 10)))
        self._scrollbar.setValue(int(offset))
        
        # Disable scrollbar when no scrolling is possible
        self._scrollbar.setEnabled(max_offset > 0)
        
        self._scrollbar.blockSignals(False)
    
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
