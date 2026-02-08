from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, QScrollBar
from PySide6.QtCore import QSize, Qt
from .canvas import StratigraphyCanvas
from .modals import ColumnSettingsModal

class StratigraphyPanel(QWidget):
    """Main widget for stratigraphy visualization and interaction."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Canvas (private)
        self._canvas = StratigraphyCanvas(self)
        self._canvas.setStyleSheet("StratigraphyCanvas { background-color: #F0F0F0; }")
        
        # Store all columns for filtering
        self._all_columns = []
        
        # Store current column configuration
        self._current_config = {
            'image': True,
            'depth': True,
            'thickness': False,
            'index': False,
            'rgb': True,
            'cielab': False,
            'munsell': True,
            'lithology': False,
            'description': False
        }
        
        # Scrollbar
        self._scrollbar = QScrollBar()
        self._scrollbar.setMinimum(0)
        self._scrollbar.setMaximum(0)
        self._scrollbar.valueChanged.connect(self._on_scrollbar_changed)
        
        # Connect canvas to update scrollbar
        self._canvas.scroll_changed = self._update_scrollbar
        
        # Overlay and popup (initially hidden)
        self._overlay = None
        self._popup = None
        
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
        toolbar.setStyleSheet("""
            QToolBar { 
                background-color: #F0F0F0; 
                border: none;
                spacing: 5px;
            }
            QPushButton {
                background-color: #F0F0F0;
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 5px 10px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border-color: #A0A0A0;
            }
            QPushButton:checked {
                background-color: #0078D4;
                color: white;
                border-color: #0078D4;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        
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
        
        # Columns button
        self.columns_btn = QPushButton("Columns")
        self.columns_btn.setFixedSize(70, 32)
        self.columns_btn.clicked.connect(self._on_columns_clicked)
        toolbar.addWidget(self.columns_btn)
        
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
    
    def _on_columns_clicked(self) -> None:
        """Handle columns button click - show popup with overlay."""
        self._show_columns_popup()
    
    def _show_columns_popup(self) -> None:
        """Create and show the columns popup with overlay."""
        # Create overlay widget (semi-transparent black background)
        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background-color: rgba(0, 0, 0, 178);")  # 70% opacity = 178/255
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        self._overlay.mousePressEvent = lambda event: self._hide_columns_popup()
        self._overlay.show()
        
        # Create popup modal
        self._popup = ColumnSettingsModal(self, current_config=self._current_config)
        
        # Connect signal to handler
        self._popup.columnsChanged.connect(self._apply_column_settings)
        
        # Calculate maximum size (60% width, 80% height of parent, respecting minimums)
        max_width = int(self.width() * 0.6)
        max_height = int(self.height() * 0.8)
        
        # Get minimum size from modal
        min_width = self._popup.minimumWidth()
        min_height = self._popup.minimumHeight()
        
        # Use calculated size with caps
        popup_width = max(min_width, min(max_width, 300))
        popup_height = max(min_height, min(max_height, 400))
        
        self._popup.resize(popup_width, popup_height)
        
        # Center the popup
        x = (self.width() - popup_width) // 2
        y = (self.height() - popup_height) // 2
        self._popup.move(x, y)
        
        self._popup.show()
        self._popup.raise_()
    
    def _hide_columns_popup(self) -> None:
        """Hide and clean up the columns popup and overlay."""
        if self._popup:
            self._popup.hide()
            self._popup.deleteLater()
            self._popup = None
        
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
    
    def _apply_column_settings(self, config: dict) -> None:
        """Apply column visibility settings from the modal.
        
        Args:
            config: Dictionary with column names as keys and visibility (bool) as values
        """
        # Store the new configuration
        self._current_config = config
        
        # Filter columns based on configuration
        # This is a simple implementation - columns are filtered by their title
        visible_columns = []
        
        for col in self._all_columns:
            col_title = col.title.lower()
            
            # Map column titles to config keys
            should_show = False
            if 'image' in col_title:
                should_show = config.get('image', True)
            elif 'depth' in col_title:
                should_show = config.get('depth', True)
            elif 'thickness' in col_title:
                should_show = config.get('thickness', False)
            elif 'index' in col_title:
                should_show = config.get('index', False)
            elif 'red' in col_title or 'green' in col_title or 'blue' in col_title:
                should_show = config.get('rgb', True)
            elif 'munsell' in col_title:
                should_show = config.get('munsell', True)
            elif 'lithology' in col_title:
                should_show = config.get('lithology', False)
            elif 'description' in col_title:
                should_show = config.get('description', False)
            else:
                # Unknown column - keep visible by default
                should_show = True
            
            if should_show:
                visible_columns.append(col)
        
        # Update canvas with filtered columns
        self._canvas.set_columns(visible_columns)
        self._canvas.update()
    
    def resizeEvent(self, event) -> None:
        """Handle resize to reposition overlay/popup if visible."""
        super().resizeEvent(event)
        
        # Reposition overlay if visible
        if self._overlay and self._overlay.isVisible():
            self._overlay.setGeometry(0, 0, self.width(), self.height())
        
        # Recenter popup if visible
        if self._popup and self._popup.isVisible():
            x = (self.width() - self._popup.width()) // 2
            y = (self.height() - self._popup.height()) // 2
            self._popup.move(x, y)
    
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
        self._all_columns.append(column)
        self._canvas.add_column(column)
    
    def set_columns(self, columns: list) -> None:
        """Set all columns at once."""
        self._all_columns = list(columns)
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
    
    def get_rows(self):
        """Get the list of row objects from the canvas."""
        return self._canvas.rows
