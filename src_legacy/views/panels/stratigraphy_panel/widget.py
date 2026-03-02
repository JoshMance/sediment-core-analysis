from __future__ import annotations
from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, QScrollBar
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap, QImage, QColor
from .canvas import StratigraphyCanvas
from .modals import ColumnSettingsModal
from .columns import BaseColumn, ImageColumn, DataColumn, RulerColumn, LayerColumn, LayerStyle

if TYPE_CHECKING:
    from models import CoreAnalysis, Image
    from models.services import CoreAnalysisService


class StratigraphyPanel(QWidget):
    """
    Main widget for stratigraphy visualization and interaction.
    
    The panel RENDERS data from a CoreAnalysis - it does NOT own layer state.
    Set up callbacks for boundary operations, then call set_analysis() to
    render the data. When user interactions occur, callbacks are invoked.
    The controller should handle callbacks, update the entity via services,
    and call refresh() to update the view.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Canvas (private)
        self._canvas = StratigraphyCanvas(self)
        self._canvas.setStyleSheet("StratigraphyCanvas { background-color: #F0F0F0; }")
        
        # Store all columns for filtering
        self._all_columns = []
        
        # Column configuration - will be populated by _discover_available_columns()
        # when set_analysis() is called. The model determines what columns exist.
        self._current_config = {}
        
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
            elif 'l*' in col_title or 'a*' in col_title or 'b*' in col_title:
                should_show = config.get('cielab', False)
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
    
    def set_analysis(self, analysis: CoreAnalysis) -> None:
        """
        Set the CoreAnalysis to render.
        
        The widget automatically creates column instances from the model.
        This is the DATA-DRIVEN VIEW PRINCIPLE: the widget discovers what
        data exists and creates appropriate visualizations.
        
        Layers are rendered from analysis.layers. The view does NOT own
        the layer state - CoreAnalysis is the authoritative source.
        """
        self._canvas.set_analysis(analysis)
        
        # Store analysis reference for column creation
        self._analysis = analysis
        
        # Discover available columns from the model
        self._current_config = self._discover_available_columns(analysis)
        
        # Create column instances from the model
        self._all_columns = self._create_columns_from_analysis(analysis)
        
        # Apply visibility settings and show columns
        self._apply_column_settings(self._current_config)
    
    def _discover_available_columns(self, analysis: CoreAnalysis) -> dict[str, bool]:
        """
        Introspect CoreAnalysis to discover available data columns.
        
        This is the MODEL-DRIVEN VIEW PRINCIPLE: the view discovers what
        data exists in the model instead of hardcoding expectations.
        
        Returns dict mapping column name -> visibility (default True for intrinsic data).
        
        Column types discovered:
        - 'image': Always available (Core.image)
        - Derived data: Core.derived.rgb, Core.derived.lab
        - Layer attributes: From analysis.schema.fields
        - View-only: 'depth', 'thickness', 'index' (not in model)
        """
        config = {}
        
        # View-only columns (always available for rendering)
        config['depth'] = True
        config['thickness'] = False
        config['index'] = False
        
        # Intrinsic: image always exists
        config['image'] = True  
        
        # Derived data from Core: introspect what exists
        core = analysis.core
        if core.derived.rgb is not None:
            config['rgb'] = True
        if core.derived.lab is not None:
            config['cielab'] = True  # UI name differs from field name
        
        # Layer categorical attributes from schema
        for field_name in analysis.schema.fields.keys():
            config[field_name] = field_name in ['munsell']  # Default visibility
        
        return config
    
    def _image_to_pixmap(self, img: Image) -> QPixmap | None:
        """Convert Image datatype to QPixmap (view-layer conversion)."""
        if img.data is None:
            return None
        h, w, c = img.data.shape
        qimage = QImage(img.data.tobytes(), w, h, c * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)
    
    def _create_columns_from_analysis(self, analysis: CoreAnalysis) -> list:
        """
        Create column instances from CoreAnalysis.
        
        This is the DATA-DRIVEN approach: the widget discovers what data exists
        in the model and creates appropriate column visualizations.
        
        View creates presentation layer (columns) from model data.
        Controller/demo just provides the model and wires callbacks.
        """
        from models.services import CoreAnalysisService
        
        columns = []
        core = analysis.core
        depth_range_mm = core.depth_range_mm or (0.0, 100.0)
        
        # View-only columns (not model data)
        columns.append(RulerColumn("Depth", width=40, unit="mm"))
        
        thickness_col = LayerColumn("Thickness", width=50, auto_thickness=True)
        thickness_col.add_category("thickness", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
        columns.append(thickness_col)
        
        index_col = LayerColumn("Index", width=40, auto_number=True)
        index_col.add_category("numbered", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
        columns.append(index_col)
        
        # Image column (intrinsic data)
        core_pixmap = self._image_to_pixmap(core.image)
        if core_pixmap:
            image_col = ImageColumn("Image", pixmap=core_pixmap, width=70)
            image_col.set_depth_range(depth_range_mm[0], depth_range_mm[1])
            columns.append(image_col)
        
        # Munsell color column with callback
        def munsell_color_callback(row):
            """Get mean color for a row's depth range."""
            from models import Layer
            start_px = int(core.depth_to_px(row.min_depth))
            end_px = int(core.depth_to_px(row.max_depth))
            layer = Layer(start_px=start_px, end_px=end_px)
            r, g, b = CoreAnalysisService.get_layer_color(analysis, layer)
            return QColor(r, g, b)
        
        munsell_col = LayerColumn("Munsell", width=50, color_callback=munsell_color_callback, hide_text=True)
        columns.append(munsell_col)
        
        # RGB data columns (derived data)
        if core.derived.rgb is not None:
            rgb_data = core.derived.rgb
            r_values = list(rgb_data.values[:, 0])
            g_values = list(rgb_data.values[:, 1])
            b_values = list(rgb_data.values[:, 2])
            
            columns.append(DataColumn("Red", data=r_values, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.GlobalColor.red)))
            columns.append(DataColumn("Green", data=g_values, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.GlobalColor.green)))
            columns.append(DataColumn("Blue", data=b_values, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.GlobalColor.blue)))
        
        # CIELAB data columns (derived data)
        if core.derived.lab is not None:
            lab_data = core.derived.lab
            l_values = list(lab_data.values[:, 0])
            a_values = list(lab_data.values[:, 1])
            b_star_values = list(lab_data.values[:, 2])
            
            columns.append(DataColumn("L*", data=l_values, min_value=0.0, max_value=100.0, width=70, color=QColor(Qt.GlobalColor.blue)))
            columns.append(DataColumn("a*", data=a_values, min_value=-128.0, max_value=127.0, width=70, color=QColor(Qt.GlobalColor.blue)))
            columns.append(DataColumn("b*", data=b_star_values, min_value=-128.0, max_value=127.0, width=70, color=QColor(Qt.GlobalColor.blue)))
        
        # Schema-based categorical columns
        for field_name in analysis.schema.fields.keys():
            if field_name not in ['munsell']:  # munsell already added above
                display_name = field_name.replace('_', ' ').title()
                columns.append(BaseColumn(display_name, width=100))
        
        return columns
    
    def refresh(self) -> None:
        """Recompute rows from analysis and repaint. Call after entity changes."""
        self._canvas.refresh()
    
    @property
    def on_boundary_add(self) -> Callable[[float], None] | None:
        """Callback invoked when user requests adding a boundary at depth (mm)."""
        return self._canvas.on_boundary_add
    
    @on_boundary_add.setter
    def on_boundary_add(self, callback: Callable[[float], None] | None) -> None:
        self._canvas.on_boundary_add = callback
    
    @property
    def on_boundary_delete(self) -> Callable[[int], None] | None:
        """Callback invoked when user requests deleting a boundary (by index)."""
        return self._canvas.on_boundary_delete
    
    @on_boundary_delete.setter
    def on_boundary_delete(self, callback: Callable[[int], None] | None) -> None:
        self._canvas.on_boundary_delete = callback
    
    @property
    def on_boundary_move(self) -> Callable[[int, float], None] | None:
        """Callback invoked when user drags a boundary to a new depth."""
        return self._canvas.on_boundary_move
    
    @on_boundary_move.setter
    def on_boundary_move(self, callback: Callable[[int, float], None] | None) -> None:
        self._canvas.on_boundary_move = callback
    
    def get_rows(self):
        """Get the list of row objects from the canvas (for rendering hints)."""
        return self._canvas.rows
