"""MunsellCalibrator — draggable overlay for Munsell calibration.

The widget is draggable anywhere within the bounds of its parent canvas widget.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from science.lib.munsell import available_hues, get_hue

_TITLE_BAR_HEIGHT = 24
_DEFAULT_WIDTH = 220

_COMBO_STYLE = (
    "QComboBox { background: #2a2a2a; color: white; font-size: 11px;"
    "            border: 1px solid #555; border-radius: 3px; padding: 1px 4px; }"
    "QComboBox:disabled { color: #666; border-color: #444; }"
    "QComboBox QAbstractItemView { background: #2a2a2a; color: white;"
    "                              selection-background-color: #0078d4; }"
)
_LABEL_STYLE = "background: transparent; color: #ccc; font-size: 11px;"
_MINI_GRID_MAX_H = 160  # cap so the calibrator doesn't grow unbounded


class _MiniGrid(QWidget):
    """Interactive miniature chip colour preview shown inside the calibrator panel."""

    cellToggled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: int = 0
        self._cols: int = 0
        self._chip_cells: frozenset[tuple[int, int]] = frozenset()
        self._colours: dict[tuple[int, int], QColor] = {}
        self._disabled_cells: set[tuple[int, int]] = set()
        self._cell_ratio: float = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_page(self, hue: dict) -> None:
        cells: list[list] = hue["cells"]
        self._rows = len(cells)
        self._cols = len(cells[0]) if cells else 0
        cells_set: set[tuple[int, int]] = set()
        for r, row in enumerate(cells):
            for c, notation in enumerate(row):
                if notation is not None:
                    cells_set.add((r, c))
        self._chip_cells = frozenset(cells_set)
        self._colours = {}
        self._disabled_cells = set()
        self._recalc_height()
        self.update()

    def set_colours(self, colours: dict[tuple[int, int], tuple[int, int, int]]) -> None:
        self._colours = {k: QColor(*v) for k, v in colours.items()}
        self.update()

    def set_cell_ratio(self, ratio: float) -> None:
        """Update the cell aspect ratio (cell_h / cell_w) and recalculate height."""
        self._cell_ratio = max(0.1, ratio)
        self._recalc_height()

    def _recalc_height(self) -> None:
        if not self._cols or not self._rows:
            return
        available_w = _DEFAULT_WIDTH - 12  # widget width minus left+right margins
        cell_px_h = (available_w / self._cols) * self._cell_ratio
        h = max(20, min(_MINI_GRID_MAX_H, int(cell_px_h * self._rows)))
        self.setFixedHeight(h)

    def clear(self) -> None:
        self._rows = 0
        self._cols = 0
        self._chip_cells = frozenset()
        self._colours = {}
        self._disabled_cells = set()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._rows and self._cols:
            pos = event.position().toPoint()
            cw = self.width() / self._cols
            ch = self.height() / self._rows
            c = int(pos.x() / cw)
            r = int(pos.y() / ch)
            if 0 <= r < self._rows and 0 <= c < self._cols and (r, c) in self._chip_cells:
                if (r, c) in self._disabled_cells:
                    self._disabled_cells.discard((r, c))
                else:
                    self._disabled_cells.add((r, c))
                self.update()
                self.cellToggled.emit()
        event.accept()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Background card
        painter.setBrush(QColor(20, 20, 20, 200))
        painter.setPen(QPen(QColor(70, 70, 70, 200), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 3, 3)
        if not self._rows or not self._cols:
            painter.end()
            return
        cw = self.width() / self._cols
        ch = self.height() / self._rows
        for r, c in self._chip_cells:
            if (r, c) in self._disabled_cells:
                painter.setBrush(QColor(30, 30, 30, 200))
                painter.setPen(QPen(QColor(80, 80, 80, 160), 1))
                painter.drawRect(QRectF(c * cw, r * ch, cw, ch))
                m = min(cw, ch) * 0.25
                painter.setPen(QPen(QColor(210, 70, 70, 220), 1.5))
                x0, y0 = c * cw, r * ch
                painter.drawLine(QPointF(x0 + m, y0 + m), QPointF(x0 + cw - m, y0 + ch - m))
                painter.drawLine(QPointF(x0 + cw - m, y0 + m), QPointF(x0 + m, y0 + ch - m))
            else:
                fill = self._colours.get((r, c), QColor(55, 55, 55, 200))
                painter.setBrush(fill)
                painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
                painter.drawRect(QRectF(c * cw, r * ch, cw, ch))


class MunsellCalibrator(QWidget):
    """Floating overlay widget draggable anywhere within the canvas viewport."""

    # Emitted when the user selects a hue; None when selection is cleared.
    hueSelected = Signal(object)  # hue dict | None
    # Emitted when the user clicks "Confirm" to sample the chip grid.
    confirmRequested = Signal()
    # Emitted when either gap slider changes. Payload: (h_px, v_px).
    gapChanged = Signal(int, int)
    # Emitted when a cell is toggled in the mini-grid.
    cellToggled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dragging = False
        self._drag_offset = QPoint()

        self.setFixedWidth(_DEFAULT_WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        self._build_ui()
        self.hide()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 8)
        layout.setSpacing(4)

        title = QLabel("Munsell Calibrator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(_TITLE_BAR_HEIGHT - 4)
        title.setStyleSheet(
            "background: transparent; color: white;"
            " font-weight: bold; font-size: 11px;"
        )
        layout.addWidget(title)

        # ── Hue row ──────────────────────────────────────────────────────
        hue_row = QHBoxLayout()
        hue_row.setContentsMargins(0, 0, 0, 0)
        hue_row.setSpacing(4)

        hue_label = QLabel("Select Hue:")
        hue_label.setFixedWidth(72)
        hue_label.setStyleSheet(_LABEL_STYLE)
        hue_row.addWidget(hue_label)

        self._hue_combo = QComboBox()
        self._hue_combo.setCursor(Qt.CursorShape.ArrowCursor)
        self._hue_combo.addItem("— select hue —")
        self._hue_combo.addItems(available_hues())
        self._hue_combo.setStyleSheet(_COMBO_STYLE)
        self._hue_combo.currentIndexChanged.connect(self._on_hue_changed)
        hue_row.addWidget(self._hue_combo, 1)

        layout.addLayout(hue_row)

        # ── Gap controls (shown only once a hue is selected) ────────────
        self._gap_widget = QWidget()
        self._gap_widget.setStyleSheet("background: transparent;")
        gap_layout = QVBoxLayout(self._gap_widget)
        gap_layout.setContentsMargins(0, 2, 0, 0)
        gap_layout.setSpacing(2)

        h_row = QHBoxLayout()
        h_row.setContentsMargins(0, 0, 0, 0)
        h_row.setSpacing(4)
        h_lbl = QLabel("H gap")
        h_lbl.setFixedWidth(36)
        h_lbl.setStyleSheet(_LABEL_STYLE)
        self._h_gap_slider = QSlider(Qt.Orientation.Horizontal)
        self._h_gap_slider.setRange(0, 30)
        self._h_gap_slider.setValue(0)
        self._h_gap_slider.setCursor(Qt.CursorShape.ArrowCursor)
        self._h_gap_label = QLabel("0 px")
        self._h_gap_label.setFixedWidth(28)
        self._h_gap_label.setStyleSheet(_LABEL_STYLE)
        h_row.addWidget(h_lbl)
        h_row.addWidget(self._h_gap_slider, 1)
        h_row.addWidget(self._h_gap_label)
        gap_layout.addLayout(h_row)

        v_row = QHBoxLayout()
        v_row.setContentsMargins(0, 0, 0, 0)
        v_row.setSpacing(4)
        v_lbl = QLabel("V gap")
        v_lbl.setFixedWidth(36)
        v_lbl.setStyleSheet(_LABEL_STYLE)
        self._v_gap_slider = QSlider(Qt.Orientation.Horizontal)
        self._v_gap_slider.setRange(0, 30)
        self._v_gap_slider.setValue(0)
        self._v_gap_slider.setCursor(Qt.CursorShape.ArrowCursor)
        self._v_gap_label = QLabel("0 px")
        self._v_gap_label.setFixedWidth(28)
        self._v_gap_label.setStyleSheet(_LABEL_STYLE)
        v_row.addWidget(v_lbl)
        v_row.addWidget(self._v_gap_slider, 1)
        v_row.addWidget(self._v_gap_label)
        gap_layout.addLayout(v_row)

        self._h_gap_slider.valueChanged.connect(self._on_gap_changed)
        self._v_gap_slider.valueChanged.connect(self._on_gap_changed)
        self._gap_widget.hide()
        layout.addWidget(self._gap_widget)

        # ── Mini grid preview ─────────────────────────────────────────────────────────────
        self._mini_grid = _MiniGrid()
        self._mini_grid.cellToggled.connect(self.cellToggled.emit)
        self._mini_grid.hide()
        layout.addWidget(self._mini_grid)

        # ── Confirm button ────────────────────────────────────────────
        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setCursor(Qt.CursorShape.ArrowCursor)
        self._confirm_btn.setFixedHeight(26)
        self._confirm_btn.setStyleSheet(
            "QPushButton { background: #0078d4; color: white; font-size: 11px;"
            "              font-weight: bold; border: 1px solid #005a9e;"
            "              border-radius: 3px; }"
            "QPushButton:hover { background: #106ebe; }"
            "QPushButton:pressed { background: #005a9e; }"
        )
        self._confirm_btn.clicked.connect(self.confirmRequested.emit)
        self._confirm_btn.setVisible(False)
        layout.addWidget(self._confirm_btn)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_hue_changed(self, index: int) -> None:
        if index == 0:
            self._confirm_btn.setVisible(False)
            self._mini_grid.clear()
            self._mini_grid.hide()
            self._gap_widget.hide()
            self._reset_gaps()
            self._after_layout_change()
            self.hueSelected.emit(None)
            return
        hue = get_hue(self._hue_combo.currentText())
        self._mini_grid.set_page(hue)
        self._mini_grid.show()
        self._gap_widget.show()
        self._confirm_btn.setVisible(True)
        self._after_layout_change()
        self.hueSelected.emit(hue)

    def _on_gap_changed(self) -> None:
        h = self._h_gap_slider.value()
        v = self._v_gap_slider.value()
        self._h_gap_label.setText(f"{h} px")
        self._v_gap_label.setText(f"{v} px")
        self.gapChanged.emit(h, v)

    def _reset_gaps(self) -> None:
        """Reset gap sliders to zero without emitting gapChanged."""
        for slider, label in (
            (self._h_gap_slider, self._h_gap_label),
            (self._v_gap_slider, self._v_gap_label),
        ):
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            label.setText("0 px")

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def disabled_cells(self) -> set[tuple[int, int]]:
        """Cells toggled off in the mini-grid preview."""
        return self._mini_grid._disabled_cells

    def set_preview_colours(
        self,
        colours: dict[tuple[int, int], tuple[int, int, int]],
        cell_ratio: float = 1.0,
    ) -> None:
        """Update the mini grid preview with sampled colours."""
        self._mini_grid.set_cell_ratio(cell_ratio)
        self._mini_grid.set_colours(colours)
        self._after_layout_change()
    def sync_to_canvas(self) -> None:
        """Re-clamp position to parent bounds (e.g. after a canvas resize)."""
        if not self.parent():
            return
        p = self.parent()
        x = max(0, min(self.x(), p.width() - self.width()))
        y = max(0, min(self.y(), p.height() - self.height()))
        self.move(x, y)
        self.raise_()

    def _after_layout_change(self) -> None:
        """Recalculate own height after children are shown/hidden, then re-clamp."""
        self.adjustSize()
        self.sync_to_canvas()

    # ── Painting ────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent dark card background.
        painter.setBrush(QColor(30, 30, 30, 210))
        painter.setPen(QPen(QColor(100, 100, 100, 220), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)

        # Divider below the title bar.
        painter.setPen(QPen(QColor(80, 80, 80, 180), 1))
        painter.drawLine(1, _TITLE_BAR_HEIGHT, self.width() - 2, _TITLE_BAR_HEIGHT)
        painter.end()
        super().paintEvent(event)

    # ── Mouse interaction ────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragging or not self.parent():
            event.accept()
            return

        p = self.parent()
        target = self.mapToParent(event.position().toPoint() - self._drag_offset)
        x = max(0, min(target.x(), p.width() - self.width()))
        y = max(0, min(target.y(), p.height() - self.height()))
        self.move(x, y)
        self.raise_()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        event.accept()
