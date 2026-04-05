"""CoreStudioPanel — blank shell panel for future core creation workflow."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class CoreStudioPanel(QWidget):
    """Placeholder panel for the Core Studio workflow.

    Currently displays a placeholder message. Future work will add
    image drop, vertical display, segmentation, and CoreEntity creation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("Drop or select an image to begin")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._placeholder, 1)
