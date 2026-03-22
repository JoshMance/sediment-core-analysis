"""Preview panel — shell chrome component.

Placeholder. Will display a thumbnail / summary for the currently
selected entity. Maintains a 1:1 aspect ratio.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel
from PySide6.QtCore import Qt


class _PreviewCanvas(QWidget):
    """Inner canvas that enforces a 1:1 aspect ratio."""

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return width


class PreviewPanel(QWidget):
    """Always-present preview panel in the shell chrome."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        panel_header = QLabel("Preview")
        panel_header.setObjectName("panelHeader")

        self._canvas = _PreviewCanvas()
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._canvas.setMinimumHeight(40)

        content = QWidget()
        content.setObjectName("previewContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._canvas)
        content_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panel_header)
        layout.addWidget(content, 1)
