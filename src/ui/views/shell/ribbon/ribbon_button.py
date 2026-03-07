"""RibbonButton -- a single action button for use inside a RibbonGroup."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QToolButton, QSizePolicy
from PySide6.QtCore import Qt, QSize


class RibbonButton(QToolButton):
    """Icon-over-text button sized for a ribbon toolbar.

    Emits the standard ``clicked`` signal.
    """

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(24, 24))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(56)
        self.setAutoRaise(True)
