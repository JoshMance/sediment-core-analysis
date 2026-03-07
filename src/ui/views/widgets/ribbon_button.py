"""RibbonButton -- a single action button for use inside a RibbonGroup."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget, QToolButton, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


class RibbonButton(QToolButton):
    """Icon-over-text button sized for a ribbon toolbar.

    Emits the standard ``clicked`` signal.
    """

    def __init__(
        self,
        text: str,
        icon_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setText(text)
        if icon_path and icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(24, 24))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(56)
        self.setAutoRaise(True)
