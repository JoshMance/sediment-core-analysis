"""StatusBar — thin view wrapper around QStatusBar.

Pure view component. Knows nothing about Store or AppController.
The presenter calls show_message() to update the left side and
show_context() to update the right side.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStatusBar

_NUM_SLOTS = 5      # Max simultaneous context items
_SLOT_MIN_WIDTH = 90


class StatusBar(QStatusBar):
    """Application status bar.

    Left side:  transient messages via show_message().
    Right side: fixed-position slots via show_context(parts).

    Slot 0 is rightmost, slot N-1 is leftmost.  Because each slot has a
    fixed minimum width they never shift position when content is added or
    removed — later slots simply show empty text.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._slots: list[QLabel] = []
        for i in range(_NUM_SLOTS):
            label = QLabel(self)
            label.setMinimumWidth(_SLOT_MIN_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if i == 0:
                label.setStyleSheet("padding-right: 12px;")
            self._slots.append(label)

        # addPermanentWidget appends left-to-right within the permanent section.
        # We want slot[0] rightmost, so add in reverse order.
        for label in reversed(self._slots):
            self.addPermanentWidget(label)

        spacer = QLabel(self)
        spacer.setFixedWidth(16)
        self.addPermanentWidget(spacer)

    def show_message(self, message: str) -> None:
        self.showMessage(message)

    def show_context(self, parts: list[str]) -> None:
        """Populate slots from parts.  slot[i] = parts[i]; extras cleared."""
        for i, label in enumerate(self._slots):
            label.setText(parts[i] if i < len(parts) else "")
