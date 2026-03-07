"""RibbonGroup -- a labelled cluster of buttons inside a ribbon tab."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
)
from PySide6.QtCore import Qt

from src.ui.views.shell.ribbon.ribbon_button import RibbonButton


class RibbonGroup(QFrame):
    """A titled row of buttons, separated from neighbours by a subtle border.

    Usage::

        grp = RibbonGroup("File")
        grp.add_button(RibbonButton("Open"))
        grp.add_button(RibbonButton("Save"))
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 0)
        layout.setSpacing(0)

        # -- row of buttons / widgets
        self._row = QHBoxLayout()
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(2)
        layout.addLayout(self._row, stretch=1)

        # -- group title at the bottom
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(8)
        label.setFont(font)
        label.setEnabled(False)  # draws in "disabled" palette color -- subtle
        layout.addWidget(label)

        self.setFrameShape(QFrame.Shape.NoFrame)

    def add_button(self, button: RibbonButton) -> None:
        self._row.addWidget(button)

    def add_widget(self, widget: QWidget) -> None:
        self._row.addWidget(widget)
