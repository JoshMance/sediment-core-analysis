"""Transient editor for a Core Studio layer's descriptive fields."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit, QWidget


class LayerDetailsDialog(QDialog):
    """Edit a layer title and note without owning core state."""

    layerUpdated = Signal(str, str, str)

    def __init__(self, layer_id: str, title: str, note: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Layer Details")
        self.setMinimumSize(360, 240)
        self._layer_id = layer_id
        self._title = QLineEdit(title)
        self._note = QPlainTextEdit(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Save")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("Title:", self._title)
        layout.addRow("Note:", self._note)
        layout.addRow(buttons)

    def _save(self) -> None:
        self.layerUpdated.emit(self._layer_id, self._title.text().strip(), self._note.toPlainText().strip())
        self.accept()