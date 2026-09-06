"""SettingsDialog — application preferences modal."""
from __future__ import annotations
from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.resources.theme.apply import is_dark


class SettingsDialog(QDialog):
    """Application settings modal.

    Currently exposes only the theme toggle. Open via ``dlg.exec()``.
    """

    themeChanged = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(420, 360)

        self._light_radio = QRadioButton("Light")
        self._dark_radio = QRadioButton("Dark")
        self._theme_group = QButtonGroup(self)
        self._theme_group.addButton(self._light_radio)
        self._theme_group.addButton(self._dark_radio)
        (self._dark_radio if is_dark() else self._light_radio).setChecked(True)

        theme_row = QWidget()
        h = QHBoxLayout(theme_row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self._light_radio)
        h.addWidget(self._dark_radio)
        h.addStretch()

        form = QFormLayout()
        form.addRow("Theme:", theme_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        dark = self._dark_radio.isChecked()
        self.themeChanged.emit(dark)
        self.accept()
