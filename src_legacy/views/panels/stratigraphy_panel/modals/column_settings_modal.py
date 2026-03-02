from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QCheckBox, QGroupBox, QScrollArea, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor


class ColumnSettingsModal(QWidget):
    """Modal dialog for configuring visible columns.
    
    This modal is DATA-DRIVEN: it dynamically creates checkboxes based on
    the columns discovered from the model, not hardcoded expectations.
    """
    
    # Signal emitted when column configuration changes
    columnsChanged = Signal(dict)
    
    def __init__(self, parent: QWidget | None = None, current_config: dict | None = None) -> None:
        super().__init__(parent)
        
        # Store current configuration (discovered from model)
        self._current_config = current_config or {}
        
        # Map column names to their checkboxes
        self._checkboxes: dict[str, QCheckBox] = {}
        
        # Set minimum size for consistent appearance
        self.setMinimumSize(120, 200)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Set white background using palette
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        pal.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the modal UI."""
        # Force light mode colors with stylesheet
        self.setStyleSheet("""
            ColumnSettingsModal {
                border-radius: 8px;
                background-color: white;
            }
            QLabel, QCheckBox, QRadioButton, QGroupBox {
                color: black;
            }
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QRadioButton {
                padding: 4px 0;
            }
            QCheckBox {
                padding: 6px 0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked:hover {
                background-color: transparent;
            }
            QCheckBox::indicator:checked:hover {
                background-color: transparent;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title bar with close button
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #d0d0d0;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 8, 10, 8)
        
        title = QLabel("Column Settings")
        title.setStyleSheet("font-size: 13px; font-weight: 600; background-color: transparent; border: none;")
        title_bar_layout.addWidget(title)
        title_bar_layout.addStretch()
        
        # Close button
        x_close_btn = QPushButton("×")
        x_close_btn.setFixedSize(24, 24)
        x_close_btn.setFlat(True)
        x_close_btn.clicked.connect(self._on_close)
        x_close_btn.setStyleSheet("""
            QPushButton {
                font-size: 22px;
                font-weight: bold;
                color: black;
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #E81123;
                color: white;
            }
        """)
        title_bar_layout.addWidget(x_close_btn)
        layout.addWidget(title_bar)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        
        scroll_content = QWidget()
        # Explicitly set white background and black text on scroll content too
        scroll_pal = scroll_content.palette()
        scroll_pal.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        scroll_pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        scroll_pal.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
        scroll_pal.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        scroll_content.setAutoFillBackground(True)
        scroll_content.setPalette(scroll_pal)
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)  # Increased spacing between sections
        
        # 1. Core group - Image
        core_group = QGroupBox("Core")
        core_layout = QVBoxLayout()
        core_layout.setContentsMargins(15, 10, 10, 10)
        core_layout.setSpacing(2)
        
        self._image_cb = QCheckBox("Image")
        self._image_cb.setChecked(True)
        self._image_cb.stateChanged.connect(lambda state: self._image_cb.setChecked(True) if state == Qt.CheckState.Unchecked.value else None)
        
        core_layout.addWidget(self._image_cb)
        core_group.setLayout(core_layout)
        content_layout.addWidget(core_group)
        
        # 2. Measurement group - Depth, Thickness, Index
        measurement_group = QGroupBox("Measurement")
        measurement_layout = QVBoxLayout()
        measurement_layout.setContentsMargins(15, 10, 10, 10)
        measurement_layout.setSpacing(2)
        
        self._depth_cb = QCheckBox("Depth")
        self._depth_cb.setChecked(True)
        self._thickness_cb = QCheckBox("Thickness")
        self._index_cb = QCheckBox("Index")
        
        measurement_layout.addWidget(self._depth_cb)
        measurement_layout.addWidget(self._thickness_cb)
        measurement_layout.addWidget(self._index_cb)
        measurement_group.setLayout(measurement_layout)
        content_layout.addWidget(measurement_group)
        
        # 3. Colour group - RGB, CIELAB, Munsell
        colour_group = QGroupBox("Colour")
        colour_layout = QVBoxLayout()
        colour_layout.setContentsMargins(15, 10, 10, 10)
        colour_layout.setSpacing(2)
        
        self._rgb_cb = QCheckBox("RGB")
        self._rgb_cb.setChecked(self._current_config.get('rgb', True))
        self._cielab_cb = QCheckBox("CIELAB")
        self._cielab_cb.setChecked(self._current_config.get('cielab', False))
        self._munsell_cb = QCheckBox("Munsell")
        self._munsell_cb.setChecked(self._current_config.get('munsell', True))
        
        colour_layout.addWidget(self._rgb_cb)
        colour_layout.addWidget(self._cielab_cb)
        colour_layout.addWidget(self._munsell_cb)
        colour_group.setLayout(colour_layout)
        content_layout.addWidget(colour_group)
        
        # 4. Geology group - Lithology, Description
        geology_group = QGroupBox("Geology")
        geology_layout = QVBoxLayout()
        geology_layout.setContentsMargins(15, 10, 10, 10)
        geology_layout.setSpacing(2)
        self._lithology_cb = QCheckBox("Lithology")
        self._lithology_cb.setChecked(self._current_config.get('lithology', False))
        self._description_cb = QCheckBox("Description")
        self._description_cb.setChecked(self._current_config.get('description', False))
        geology_layout.addWidget(self._lithology_cb)
        geology_layout.addWidget(self._description_cb)
        geology_group.setLayout(geology_layout)
        content_layout.addWidget(geology_group)
        
        content_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # Button bar at bottom
        button_bar = QWidget()
        button_bar.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #d0d0d0;")
        button_bar_layout = QHBoxLayout(button_bar)
        button_bar_layout.setContentsMargins(20, 15, 20, 15)
        button_bar_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(32)
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self._on_close)
        cancel_btn.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #b0b0b0;
            }
        """)
        button_bar_layout.addWidget(cancel_btn)
        
        # Confirm button
        confirm_btn = QPushButton("Apply Changes")
        confirm_btn.setFixedHeight(32)
        confirm_btn.setMinimumWidth(120)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
                border-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
                border-color: #005a9e;
            }
        """)
        button_bar_layout.addWidget(confirm_btn)
        layout.addWidget(button_bar)
    
    def _on_close(self) -> None:
        """Handle close button click."""
        # Trigger parent's hide method
        if self.parent() and hasattr(self.parent(), '_hide_columns_popup'):
            self.parent()._hide_columns_popup()
    
    def _on_confirm(self) -> None:
        """Handle confirm button click - collect configuration from all discovered columns."""
        # Build configuration data-driven from all checkboxes that were dynamically created
        config = {}
        
        # Collect from all checkboxes (handles dynamically discovered columns)
        if hasattr(self, '_checkboxes'):
            config = {
                col_name: checkbox.isChecked()
                for col_name, checkbox in self._checkboxes.items()
            }
        else:
            # Fallback to hardcoded approach (backward compatibility)
            config = {
                'image': getattr(self, '_image_cb', None).isChecked() if hasattr(self, '_image_cb') else True,
                'depth': getattr(self, '_depth_cb', None).isChecked() if hasattr(self, '_depth_cb') else True,
                'thickness': getattr(self, '_thickness_cb', None).isChecked() if hasattr(self, '_thickness_cb') else False,
                'index': getattr(self, '_index_cb', None).isChecked() if hasattr(self, '_index_cb') else False,
                'rgb': getattr(self, '_rgb_cb', None).isChecked() if hasattr(self, '_rgb_cb') else True,
                'cielab': getattr(self, '_cielab_cb', None).isChecked() if hasattr(self, '_cielab_cb') else False,
                'munsell': getattr(self, '_munsell_cb', None).isChecked() if hasattr(self, '_munsell_cb') else True,
                'lithology': getattr(self, '_lithology_cb', None).isChecked() if hasattr(self, '_lithology_cb') else False,
                'description': getattr(self, '_description_cb', None).isChecked() if hasattr(self, '_description_cb') else False
            }
        
        # Emit signal with configuration
        self.columnsChanged.emit(config)
        
        # Hide modal
        if self.parent() and hasattr(self.parent(), '_hide_columns_popup'):
            self.parent()._hide_columns_popup()
