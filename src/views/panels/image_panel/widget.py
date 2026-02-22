from __future__ import annotations
from typing import Callable

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton, 
                                QLabel, QLineEdit, QSlider)
from PySide6.QtGui import QPixmap, QDoubleValidator, QImage
from PySide6.QtCore import QSize, Qt, QObject, Signal

import numpy as np

from models import Image
from .canvas import ImageCanvas, MODE_PAN, MODE_SELECT, MODE_CALIBRATE


class ImagePanelSignals(QObject):
    """Signals emitted by ImagePanel."""
    imageChanged = Signal(object)  # Image datatype

class ImagePanel(QWidget):
    """
    Main widget providing image display with pan/zoom interaction.
    
    The panel RENDERS an Image - it does NOT own domain logic.
    When user confirms selection or calibration, callbacks are invoked.
    The controller (demo) handles callbacks and decides what to do.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Signals
        self.signals = ImagePanelSignals()

        # Internal canvas
        self.canvas = ImageCanvas(self)

        # State
        self._image: Image | None = None  # Current Image datatype
        self._current_mode = MODE_PAN
        self._calibration_mm_per_pixel: float | None = None  # Set after calibration
        
        # Callbacks (set by controller/demo)
        self.on_selection_confirmed: Callable[[QPixmap, float | None], None] | None = None
        self.on_calibration_confirmed: Callable[[float], None] | None = None

        # Toolbar
        self.toolbar = self._create_toolbar()

        # Preview widget (bottom right corner overlay)
        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setStyleSheet("border: 2px solid white; background-color: rgba(255, 255, 255, 200);")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.hide()

        # Calibration input (overlay on canvas)
        self.calib_input_widget = self._create_calibration_input()
        self.calib_input_widget.hide()

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with image interaction controls."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Zoom buttons
        self.zoom_in_btn = self._create_tool_button("Zoom In", "+")
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        toolbar.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = self._create_tool_button("Zoom Out", "−")
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        toolbar.addWidget(self.zoom_out_btn)

        toolbar.addSeparator()

        # Rotation slider
        toolbar.addWidget(QLabel("Rotate:"))
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setFixedWidth(150)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setTickInterval(45)
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)
        toolbar.addWidget(self.rotation_slider)
        
        self.rotation_label = QLabel("0°")
        self.rotation_label.setFixedWidth(35)
        toolbar.addWidget(self.rotation_label)

        toolbar.addSeparator()

        # Mode buttons
        self.select_btn = self._create_tool_button("Select Region", "Select")
        self.select_btn.setCheckable(True)
        self.select_btn.clicked.connect(self._on_select_clicked)
        toolbar.addWidget(self.select_btn)

        self.calibrate_btn = self._create_tool_button("Calibrate Scale", "Calibrate")
        self.calibrate_btn.setCheckable(True)
        self.calibrate_btn.clicked.connect(self._on_calibrate_clicked)
        toolbar.addWidget(self.calibrate_btn)

        toolbar.addSeparator()

        # Confirm/Cancel buttons (initially hidden)
        self.confirm_btn = self._create_tool_button("Confirm", "✓")
        self.confirm_btn.clicked.connect(self._on_confirm_clicked)
        self.confirm_action = toolbar.addWidget(self.confirm_btn)
        self.confirm_action.setVisible(False)

        self.cancel_btn = self._create_tool_button("Cancel", "✗")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_action = toolbar.addWidget(self.cancel_btn)
        self.cancel_action.setVisible(False)

        return toolbar

    def _create_tool_button(self, tooltip: str, text: str) -> QPushButton:
        """Create a consistently styled toolbar button."""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setFixedSize(70, 32)
        return button

    def _create_calibration_input(self) -> QWidget:
        """Create the calibration input widget (distance + unit)."""
        widget = QWidget(self.canvas)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.calib_input = QLineEdit()
        self.calib_input.setFixedWidth(60)
        self.calib_input.setPlaceholderText("0.0")
        validator = QDoubleValidator(0.0, 10000.0, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.calib_input.setValidator(validator)
        self.calib_input.textChanged.connect(self._on_calib_input_changed)
        
        unit_label = QLabel("mm")
        
        layout.addWidget(self.calib_input)
        layout.addWidget(unit_label)
        
        widget.setStyleSheet("background-color: white; border: 1px solid black; border-radius: 3px;")
        return widget

    def resizeEvent(self, event) -> None:
        """Position overlay widgets on resize."""
        super().resizeEvent(event)
        # Position preview in bottom right
        self.preview_label.move(
            self.width() - self.preview_label.width() - 10,
            self.height() - self.preview_label.height() - 10
        )
        # Position calibration input at center of canvas (will update during calibration)
        self._update_calibration_input_position()

    def _update_calibration_input_position(self) -> None:
        """Position calibration input at midpoint of calibration line."""
        if not self.calib_input_widget.isVisible():
            return
        
        points = self.canvas.get_calibration_points()
        if points:
            p1, p2 = points
            # Get midpoint in image coords
            mid_img_x = (p1.x() + p2.x()) / 2
            mid_img_y = (p1.y() + p2.y()) / 2
            
            # Transform to widget coordinates
            # Account for image offset (centered), zoom, and pan
            img_offset_x = (self.canvas.width() / self.canvas._zoom - self.canvas._pixmap.width()) / 2
            img_offset_y = (self.canvas.height() / self.canvas._zoom - self.canvas._pixmap.height()) / 2
            
            widget_x = (mid_img_x + img_offset_x) * self.canvas._zoom + self.canvas._pan_x
            widget_y = (mid_img_y + img_offset_y) * self.canvas._zoom + self.canvas._pan_y
            
            # Position input widget above the line
            self.calib_input_widget.move(
                int(widget_x - self.calib_input_widget.width() / 2),
                int(widget_y - self.calib_input_widget.height() - 15)
            )

    def _on_rotation_changed(self, angle: int) -> None:
        """Handle rotation slider change."""
        self.canvas.set_rotation(angle)
        self.rotation_label.setText(f"{angle}°")
        # Update calibration input position if visible
        if self.calib_input_widget.isVisible():
            self._update_calibration_input_position()

    def _on_select_clicked(self) -> None:
        """Handle Select button toggle."""
        if self.select_btn.isChecked():
            # Deactivate calibration if active
            if self.calibrate_btn.isChecked():
                self._deactivate_calibration()
            
            # Disable calibrate button while select is active
            self.calibrate_btn.setEnabled(False)
            
            # Activate selection mode
            self._current_mode = MODE_SELECT
            self.canvas.set_mode(MODE_SELECT)
            self.canvas.set_selection_visible(True)
            self.confirm_action.setVisible(True)
            self.cancel_action.setVisible(True)
        else:
            self._deactivate_selection()

    def _on_calibrate_clicked(self) -> None:
        """Handle Calibrate button toggle."""
        if self.calibrate_btn.isChecked():
            # Deactivate selection if active
            if self.select_btn.isChecked():
                self._deactivate_selection()
            
            # Disable select button while calibrate is active
            self.select_btn.setEnabled(False)
            
            # Activate calibration mode
            self._current_mode = MODE_CALIBRATE
            self.canvas.set_mode(MODE_CALIBRATE)
            self.canvas.set_calibration_visible(True)
            self.calib_input_widget.show()
            self.calib_input.clear()
            self.confirm_action.setVisible(True)
            self.confirm_btn.setEnabled(False)  # Disabled until input provided
            self.cancel_action.setVisible(True)
            
            # Connect signal to update input position
            self.canvas.calibration_changed.connect(self._update_calibration_input_position)
            self._update_calibration_input_position()
        else:
            self._deactivate_calibration()

    def _on_confirm_clicked(self) -> None:
        """Handle Confirm button click."""
        if self._current_mode == MODE_SELECT:
            # Extract selected region
            pixmap = self.canvas.get_selection_pixmap()
            if pixmap:
                # Show preview
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.show()
                
                # Invoke callback if set (controller handles domain logic)
                if self.on_selection_confirmed is not None:
                    self.on_selection_confirmed(pixmap, self._calibration_mm_per_pixel)
            
            self._deactivate_selection()
        
        elif self._current_mode == MODE_CALIBRATE:
            # Calculate calibration
            distance_mm = float(self.calib_input.text() or "0")
            distance_pixels = self.canvas.get_calibration_pixel_distance()
            
            if distance_mm > 0 and distance_pixels > 0:
                self._calibration_mm_per_pixel = distance_mm / distance_pixels
                
                # Invoke callback if set (controller can react to calibration)
                if self.on_calibration_confirmed is not None:
                    self.on_calibration_confirmed(self._calibration_mm_per_pixel)
            
            self._deactivate_calibration()

    def _on_cancel_clicked(self) -> None:
        """Handle Cancel button click."""
        if self._current_mode == MODE_SELECT:
            self._deactivate_selection()
        elif self._current_mode == MODE_CALIBRATE:
            self._deactivate_calibration()

    def _on_calib_input_changed(self) -> None:
        """Enable confirm button when valid input is provided."""
        text = self.calib_input.text()
        self.confirm_btn.setEnabled(len(text) > 0 and float(text or "0") > 0)

    def _deactivate_selection(self) -> None:
        """Deactivate selection mode."""
        self.select_btn.setChecked(False)
        self.canvas.set_selection_visible(False)
        self.canvas.set_mode(MODE_PAN)
        self.confirm_action.setVisible(False)
        self.cancel_action.setVisible(False)
        self.calibrate_btn.setEnabled(True)  # Re-enable calibrate button
        self._current_mode = MODE_PAN

    def _deactivate_calibration(self) -> None:
        """Deactivate calibration mode."""
        self.calibrate_btn.setChecked(False)
        self.canvas.set_calibration_visible(False)
        self.canvas.set_mode(MODE_PAN)
        self.calib_input_widget.hide()
        self.confirm_action.setVisible(False)
        self.cancel_action.setVisible(False)
        self.select_btn.setEnabled(True)  # Re-enable select button
        self._current_mode = MODE_PAN
        try:
            self.canvas.calibration_changed.disconnect(self._update_calibration_input_position)
        except:
            pass  # Already disconnected

    # -------- Public API --------

    def set_image(self, image: Image | None) -> None:
        """Set the Image datatype to display."""
        self._image = image
        pixmap = self._image_to_pixmap(image) if image else None
        self.canvas.set_pixmap(pixmap)
        self.signals.imageChanged.emit(image)

    def get_image(self) -> Image | None:
        """Get the current Image datatype."""
        return self._image

    def clear(self) -> None:
        """Clear the displayed image."""
        self._image = None
        self.canvas.set_pixmap(None)

    # -------- Internal Conversion --------

    def _image_to_pixmap(self, image: Image) -> QPixmap | None:
        """Convert Image datatype to QPixmap for rendering."""
        if image.data is None:
            return None
        
        # Image.data is (height, width, 3) RGB numpy array
        h, w, channels = image.data.shape
        bytes_per_line = channels * w
        
        # Create QImage from numpy data (expects contiguous array)
        qimage = QImage(
            image.data.tobytes(),
            w, h,
            bytes_per_line,
            QImage.Format_RGB888
        )
        
        return QPixmap.fromImage(qimage)

    def _pixmap_to_ndarray(self, pixmap: QPixmap) -> np.ndarray:
        """Convert QPixmap to numpy array (RGB)."""
        qimage = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
        w, h = qimage.width(), qimage.height()
        
        # Get raw bytes and reshape
        ptr = qimage.bits()
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 3)).copy()
        return arr
