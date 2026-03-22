"""Preview panel — shell chrome component.

Displays a metadata summary for the currently selected entity in
VariablesList. Driven entirely by VariablesPresenter.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt


class PreviewPanel(QWidget):
    """Always-present metadata summary panel in the shell chrome.

    Public API (called by VariablesPresenter):
        show_entity(rows)  — display a list of (label, value) pairs
        clear()            — reset to the empty/placeholder state
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        panel_header = QLabel("Preview")
        panel_header.setObjectName("panelHeader")

        self._content = QWidget()
        self._content.setObjectName("previewContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(4)
        self._content_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panel_header)
        layout.addWidget(self._content, 1)

    # ── Public API ────────────────────────────────────────────────

    def show_entity(self, rows: list[tuple[str, str]]) -> None:
        """Populate the panel with (label, value) metadata rows."""
        self._clear_rows()
        for label, value in rows:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(1)
            lbl = QLabel(label)
            lbl.setObjectName("previewLabel")
            val = QLabel(value)
            val.setObjectName("previewValue")
            val.setWordWrap(True)
            row_layout.addWidget(lbl)
            row_layout.addWidget(val)
            self._content_layout.insertWidget(self._content_layout.count() - 1, row)

    def clear(self) -> None:
        """Reset to empty state."""
        self._clear_rows()

    # ── Internal ──────────────────────────────────────────────────

    def _clear_rows(self) -> None:
        # Remove everything except the trailing stretch (last item)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
