"""FilterPanel — view widget for the core image filter stack.

Displays the current filter stack as an ordered list of rows.
Each row lets the user enable/disable, adjust, reorder, or remove a filter.
An "Add filter" control at the bottom lets users append new filters.

Pure view — emits ``filterStackChanged(list[dict])`` when anything changes.
Never imports domain or application code.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# Display label -> filter type key (must match science.lib.filters.FILTER_REGISTRY)
_FILTER_OPTIONS: list[tuple[str, str]] = [
    ("Brightness", "brightness"),
    ("Contrast",   "contrast"),
    ("Gamma",      "gamma"),
]

_FILTER_DEFAULTS: dict[str, float] = {
    "brightness": 1.0,
    "contrast":   1.0,
    "gamma":      1.0,
}

_FILTER_RANGES: dict[str, tuple[float, float, float]] = {
    # type: (min, max, step)
    "brightness": (0.0,  3.0, 0.05),
    "contrast":   (0.0,  3.0, 0.05),
    "gamma":      (0.1,  3.0, 0.05),
}

_LABEL_FOR_TYPE = {key: label for label, key in _FILTER_OPTIONS}


class _FilterRow(QWidget):
    """One row in the filter list."""

    changed = Signal()
    remove_requested = Signal(object)   # self
    move_up_requested = Signal(object)  # self
    move_down_requested = Signal(object)

    def __init__(self, filter_dict: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._type = filter_dict["type"]
        enabled = filter_dict.get("enabled", True)
        value = filter_dict.get("value", _FILTER_DEFAULTS.get(self._type, 1.0))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(4)

        # Up / down buttons
        up_btn = QToolButton()
        up_btn.setText("↑")
        up_btn.setFixedSize(20, 20)
        up_btn.clicked.connect(lambda: self.move_up_requested.emit(self))
        layout.addWidget(up_btn)

        down_btn = QToolButton()
        down_btn.setText("↓")
        down_btn.setFixedSize(20, 20)
        down_btn.clicked.connect(lambda: self.move_down_requested.emit(self))
        layout.addWidget(down_btn)

        # Enable checkbox
        self._check = QCheckBox()
        self._check.setChecked(enabled)
        self._check.toggled.connect(self._on_changed)
        layout.addWidget(self._check)

        # Type label
        label = QLabel(_LABEL_FOR_TYPE.get(self._type, self._type))
        label.setFixedWidth(72)
        layout.addWidget(label)

        # Value spinbox
        lo, hi, step = _FILTER_RANGES.get(self._type, (0.0, 10.0, 0.1))
        self._spin = QDoubleSpinBox()
        self._spin.setRange(lo, hi)
        self._spin.setSingleStep(step)
        self._spin.setDecimals(2)
        self._spin.setValue(value)
        self._spin.setFixedWidth(70)
        self._spin.valueChanged.connect(self._on_changed)
        layout.addWidget(self._spin)

        layout.addStretch()

        # Remove button
        remove_btn = QToolButton()
        remove_btn.setText("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(remove_btn)

    # ── Public helpers ─────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "type": self._type,
            "value": self._spin.value(),
            "enabled": self._check.isChecked(),
        }

    def set_from_dict(self, d: dict) -> None:
        self._spin.blockSignals(True)
        self._check.blockSignals(True)
        self._spin.setValue(d.get("value", _FILTER_DEFAULTS.get(self._type, 1.0)))
        self._check.setChecked(d.get("enabled", True))
        self._spin.blockSignals(False)
        self._check.blockSignals(False)

    # ── Internal ───────────────────────────────────────────────

    def _on_changed(self) -> None:
        self.changed.emit()


class FilterPanel(QWidget):
    """Collapsible panel that exposes the filter stack as an editable list."""

    filterStackChanged = Signal(list)  # list[dict]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[_FilterRow] = []
        self._suppress_emit = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Toggle header ──────────────────────────────────────
        self._toggle_btn = QPushButton("▶  Filters")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(False)
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setFixedHeight(26)
        self._toggle_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._toggle_btn.toggled.connect(self._on_toggle)
        outer.addWidget(self._toggle_btn)

        # ── Collapsible body ───────────────────────────────────
        self._body = QFrame()
        self._body.setFrameShape(QFrame.Shape.StyledPanel)
        self._body.setVisible(False)
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(4, 4, 4, 4)
        body_layout.setSpacing(2)

        # Scroll area for the filter rows
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setFixedHeight(160)

        self._rows_widget = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(1)
        self._rows_layout.addStretch()
        self._scroll_area.setWidget(self._rows_widget)
        body_layout.addWidget(self._scroll_area)

        # ── Add filter row ─────────────────────────────────────
        add_row = QHBoxLayout()
        self._add_combo = QComboBox()
        for label, _ in _FILTER_OPTIONS:
            self._add_combo.addItem(label)
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(48)
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self._add_combo, 1)
        add_row.addWidget(add_btn)
        body_layout.addLayout(add_row)

        outer.addWidget(self._body)

    # ── Public API ─────────────────────────────────────────────

    def set_stack(self, stack: list[dict]) -> None:
        """Rebuild the row list from *stack*.  Does not emit filterStackChanged."""
        self._suppress_emit = True
        try:
            self._clear_rows()
            for item in stack:
                self._append_row(item)
        finally:
            self._suppress_emit = False

    def current_stack(self) -> list[dict]:
        return [row.to_dict() for row in self._rows]

    # ── Internal ───────────────────────────────────────────────

    def _on_toggle(self, checked: bool) -> None:
        self._toggle_btn.setText(("▼" if checked else "▶") + "  Filters")
        self._body.setVisible(checked)

    def _on_add(self) -> None:
        label = self._add_combo.currentText()
        type_key = next((k for lbl, k in _FILTER_OPTIONS if lbl == label), None)
        if type_key is None:
            return
        self._append_row({"type": type_key, "value": _FILTER_DEFAULTS[type_key], "enabled": True})
        self._emit()

    def _append_row(self, filter_dict: dict) -> None:
        row = _FilterRow(filter_dict, self._rows_widget)
        row.changed.connect(self._emit)
        row.remove_requested.connect(self._on_remove)
        row.move_up_requested.connect(self._on_move_up)
        row.move_down_requested.connect(self._on_move_down)
        self._rows.append(row)
        # Insert before the trailing stretch (last item in layout)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)

    def _clear_rows(self) -> None:
        for row in self._rows:
            self._rows_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _on_remove(self, row: _FilterRow) -> None:
        idx = self._rows.index(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._rows.pop(idx)
        self._emit()

    def _on_move_up(self, row: _FilterRow) -> None:
        idx = self._rows.index(row)
        if idx == 0:
            return
        self._rows[idx], self._rows[idx - 1] = self._rows[idx - 1], self._rows[idx]
        self._rows_layout.removeWidget(row)
        self._rows_layout.insertWidget(idx - 1, row)
        self._emit()

    def _on_move_down(self, row: _FilterRow) -> None:
        idx = self._rows.index(row)
        if idx >= len(self._rows) - 1:
            return
        self._rows[idx], self._rows[idx + 1] = self._rows[idx + 1], self._rows[idx]
        self._rows_layout.removeWidget(row)
        self._rows_layout.insertWidget(idx + 1, row)
        self._emit()

    def _emit(self) -> None:
        if not self._suppress_emit:
            self.filterStackChanged.emit(self.current_stack())
