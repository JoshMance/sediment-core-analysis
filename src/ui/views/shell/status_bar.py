"""StatusBar — thin view wrapper around QStatusBar.

Pure view component. Knows nothing about Store or AppController.
The presenter calls show_message() to update it.
"""
from __future__ import annotations

from PySide6.QtWidgets import QStatusBar


class StatusBar(QStatusBar):
    """Application status bar."""

    def show_message(self, message: str) -> None:
        self.showMessage(message)
