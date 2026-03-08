"""Custom QFileIconProvider that serves the sedivis file icon for .sedivis files."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider

_SEDIVIS_ICON = Path(__file__).parent / "logo" / "sedivis_file_icon.svg"


class SedivisIconProvider(QFileIconProvider):
    """Returns the sedivis file icon for .sedivis files; delegates all others."""

    def __init__(self) -> None:
        super().__init__()
        self._icon = QIcon(str(_SEDIVIS_ICON))

    def icon(self, arg: QFileIconProvider.IconType | QFileInfo) -> QIcon:  # type: ignore[override]
        if isinstance(arg, QFileInfo) and arg.suffix().lower() == "sedivis":
            return self._icon
        return super().icon(arg)
