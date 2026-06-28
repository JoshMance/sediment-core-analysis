"""CoreImagePanel — displays a core image with pan/zoom/rotate and crop tools."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QPushButton, QLabel, QSpinBox, QComboBox,
)

from science.lib import available_illuminants
from src.ui.views.panels.core_image_panel.canvas import ImageCanvas
from src.ui.views.panels.core_image_panel.filter_panel import FilterPanel


class CoreImagePanel(QWidget):
    """Runtime panel for inspecting a single core image.

    Pure view. Emits signals only — the Presenter handles all domain logic.
    Created at runtime by WorkspacePresenter when a core is opened.
    """

    # Emitted when the user confirms a crop.
    # Carries the crop region as (x, y, w, h) in image-space pixels.
    cropConfirmed = Signal(float, float, float, float)
    # Emitted when distance calibration is confirmed; carries mm_per_px.
    distanceCalibrated = Signal(float)
    # Emitted when the user selects an illuminant; carries key str or None.
    illuminantChanged = Signal(object)
    # Emitted when the filter stack changes; carries the new list[dict].
    filterStackChanged = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.canvas = ImageCanvas(self)
        self.canvas.rulerComplete.connect(self._on_ruler_complete)
        self.canvas.rulerCancelled.connect(self._deactivate_ruler)
        self.canvas.munsellClosed.connect(self._on_munsell_closed)
        self.toolbar = self._build_toolbar()
        self._filter_panel = FilterPanel(self)
        self._filter_panel.filterStackChanged.connect(self.filterStackChanged)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self._filter_panel)

    # ── Public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the image to display and reset crop state."""
        self.canvas.set_pixmap(pixmap)
        self._deactivate_crop()
        self._deactivate_ruler()

    def set_illuminant(self, key: str | None) -> None:
        """Update the illuminant combo without emitting illuminantChanged."""
        self._illuminant_combo.blockSignals(True)
        idx = 0
        if key is not None:
            for i in range(self._illuminant_combo.count()):
                if self._illuminant_combo.itemData(i) == key:
                    idx = i
                    break
        self._illuminant_combo.setCurrentIndex(idx)
        self._illuminant_combo.blockSignals(False)

    def set_filter_stack(self, stack: list[dict]) -> None:
        """Sync the filter panel to *stack* without emitting filterStackChanged."""
        self._filter_panel.set_stack(stack)

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
        self._rotation_spinbox = QSpinBox()
        self._rotation_spinbox.setRange(0, 359)
        self._rotation_spinbox.setValue(0)
        self._rotation_spinbox.setSuffix("°")
        self._rotation_spinbox.setWrapping(True)
        self._rotation_spinbox.setFixedWidth(72)
        self._rotation_spinbox.valueChanged.connect(self._on_rotation_changed)
        tb.addWidget(self._rotation_spinbox)

        tb.addSeparator()

        self._crop_btn = QPushButton("Crop")
        self._crop_btn.setToolTip("Crop a region of this image")
        self._crop_btn.setCheckable(True)
        self._crop_btn.setFixedSize(60, 28)
        self._crop_btn.clicked.connect(self._on_crop_toggled)
        tb.addWidget(self._crop_btn)

        tb.addSeparator()

        self._confirm_btn = QPushButton("✓")
        self._confirm_btn.setToolTip("Confirm crop")
        self._confirm_btn.setFixedSize(32, 28)
        self._confirm_btn.clicked.connect(self._on_confirm_clicked)
        self._confirm_action = tb.addWidget(self._confirm_btn)
        self._confirm_action.setVisible(False)

        self._cancel_btn = QPushButton("✗")
        self._cancel_btn.setToolTip("Cancel crop")
        self._cancel_btn.setFixedSize(32, 28)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        self._cancel_action = tb.addWidget(self._cancel_btn)
        self._cancel_action.setVisible(False)

        tb.addSeparator()

        self._ruler_btn = QPushButton("Calibrate Distance")
        self._ruler_btn.setToolTip("Click two points on the image, then enter the real distance in mm")
        self._ruler_btn.setCheckable(True)
        self._ruler_btn.setFixedHeight(28)
        self._ruler_btn.clicked.connect(self._on_ruler_toggled)
        tb.addWidget(self._ruler_btn)

        tb.addSeparator()

        self._calibrate_btn = QPushButton("Calibrate Munsell")
        self._calibrate_btn.setToolTip("Toggle Munsell colour calibrator")
        self._calibrate_btn.setCheckable(True)
        self._calibrate_btn.setFixedHeight(28)
        self._calibrate_btn.clicked.connect(self._on_calibrate_toggled)
        tb.addWidget(self._calibrate_btn)

        tb.addSeparator()

        tb.addWidget(QLabel("Illuminant:"))
        self._illuminant_combo = QComboBox()
        self._illuminant_combo.setToolTip("Select the capture illuminant for this core")
        self._illuminant_combo.addItem("—", userData=None)
        for key, name in available_illuminants().items():
            self._illuminant_combo.addItem(name, userData=key)
        self._illuminant_combo.currentIndexChanged.connect(self._on_illuminant_changed)
        tb.addWidget(self._illuminant_combo)

        return tb

    # ── Slots ─────────────────────────────────────────────────

    def _on_rotation_changed(self, angle: int) -> None:
        self.canvas.set_rotation(angle)

    def _on_crop_toggled(self) -> None:
        if self._crop_btn.isChecked():
            self.canvas.set_crop_visible(True)
            self._confirm_action.setVisible(True)
            self._cancel_action.setVisible(True)
        else:
            self._deactivate_crop()

    def _on_confirm_clicked(self) -> None:
        rect = self.canvas.get_crop_rect()
        if rect:
            self.cropConfirmed.emit(rect.x(), rect.y(), rect.width(), rect.height())
        self._deactivate_crop()

    def _on_cancel_clicked(self) -> None:
        self._deactivate_crop()

    def _on_calibrate_toggled(self) -> None:
        self.canvas.set_calibrator_visible(self._calibrate_btn.isChecked())

    def _on_munsell_closed(self) -> None:
        self._calibrate_btn.setChecked(False)

    def _on_illuminant_changed(self, index: int) -> None:
        self.illuminantChanged.emit(self._illuminant_combo.itemData(index))

    def _on_ruler_toggled(self) -> None:
        self.canvas.set_ruler_mode(self._ruler_btn.isChecked())

    def _on_ruler_complete(self, px_distance: float) -> None:
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibrate Distance")
        layout = QFormLayout(dialog)
        layout.addRow(QLabel(f"Pixel distance: {px_distance:.1f} px"))
        mm_spin = QDoubleSpinBox()
        mm_spin.setRange(0.01, 100_000.0)
        mm_spin.setDecimals(2)
        mm_spin.setSuffix(" mm")
        mm_spin.setValue(10.0)
        layout.addRow("Real-world distance:", mm_spin)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            mm = mm_spin.value()
            mm_per_px = mm / px_distance
            self.distanceCalibrated.emit(mm_per_px)
            self._deactivate_ruler()
        else:
            self.canvas.reset_ruler_p2()

    def _deactivate_ruler(self) -> None:
        self._ruler_btn.setChecked(False)
        self.canvas.set_ruler_mode(False)

    def _deactivate_crop(self) -> None:
        self._crop_btn.setChecked(False)
        self.canvas.set_crop_visible(False)
        self._confirm_action.setVisible(False)
        self._cancel_action.setVisible(False)
