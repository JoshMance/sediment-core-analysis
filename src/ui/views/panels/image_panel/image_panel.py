"""ImagePanel — displays an image with pan/zoom/rotate and selection tools."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QPushButton, QLabel, QSlider,
)

from src.ui.views.panels.image_panel.canvas import ImageCanvas


class ImagePanel(QWidget):
    """Runtime panel for inspecting a single image entity.

    Pure view. Emits signals only — the Presenter handles all domain logic.
    Created at runtime by WorkspacePresenter when an image entity is opened.
    """

    # Emitted when the user confirms a selection; carries the cropped QPixmap.
    selectionConfirmed = Signal(object)  # QPixmap

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.canvas = ImageCanvas(self)
        self.toolbar = self._build_toolbar()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

    # ── Public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the image to display and reset selection state."""
        self.canvas.set_pixmap(pixmap)
        self._deactivate_selection()

    # ── Toolbar ───────────────────────────────────────────────

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))

        zoom_in = QPushButton("+")
        zoom_in.setToolTip("Zoom in")
        zoom_in.setFixedSize(32, 28)
        zoom_in.clicked.connect(self.canvas.zoom_in)
        tb.addWidget(zoom_in)

        zoom_out = QPushButton("−")
        zoom_out.setToolTip("Zoom out")
        zoom_out.setFixedSize(32, 28)
        zoom_out.clicked.connect(self.canvas.zoom_out)
        tb.addWidget(zoom_out)

        tb.addSeparator()

        tb.addWidget(QLabel("Rotate:"))
        self._rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self._rotation_slider.setRange(0, 360)
        self._rotation_slider.setValue(0)
        self._rotation_slider.setFixedWidth(140)
        self._rotation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._rotation_slider.setTickInterval(45)
        self._rotation_slider.valueChanged.connect(self._on_rotation_changed)
        tb.addWidget(self._rotation_slider)

        self._rotation_label = QLabel("0°")
        self._rotation_label.setFixedWidth(36)
        tb.addWidget(self._rotation_label)

        tb.addSeparator()

        self._select_btn = QPushButton("Select")
        self._select_btn.setToolTip("Select a region to create a core")
        self._select_btn.setCheckable(True)
        self._select_btn.setFixedSize(60, 28)
        self._select_btn.clicked.connect(self._on_select_toggled)
        tb.addWidget(self._select_btn)

        tb.addSeparator()

        self._confirm_btn = QPushButton("✓")
        self._confirm_btn.setToolTip("Confirm selection — creates a CoreEntity")
        self._confirm_btn.setFixedSize(32, 28)
        self._confirm_btn.clicked.connect(self._on_confirm_clicked)
        self._confirm_action = tb.addWidget(self._confirm_btn)
        self._confirm_action.setVisible(False)

        self._cancel_btn = QPushButton("✗")
        self._cancel_btn.setToolTip("Cancel selection")
        self._cancel_btn.setFixedSize(32, 28)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        self._cancel_action = tb.addWidget(self._cancel_btn)
        self._cancel_action.setVisible(False)

        return tb

    # ── Slots ─────────────────────────────────────────────────

    def _on_rotation_changed(self, angle: int) -> None:
        self.canvas.set_rotation(angle)
        self._rotation_label.setText(f"{angle}°")

    def _on_select_toggled(self) -> None:
        if self._select_btn.isChecked():
            self.canvas.set_selection_visible(True)
            self._confirm_action.setVisible(True)
            self._cancel_action.setVisible(True)
        else:
            self._deactivate_selection()

    def _on_confirm_clicked(self) -> None:
        pixmap = self.canvas.get_selection_pixmap()
        if pixmap:
            self.selectionConfirmed.emit(pixmap)
        self._deactivate_selection()

    def _on_cancel_clicked(self) -> None:
        self._deactivate_selection()

    def _deactivate_selection(self) -> None:
        self._select_btn.setChecked(False)
        self.canvas.set_selection_visible(False)
        self._confirm_action.setVisible(False)
        self._cancel_action.setVisible(False)
