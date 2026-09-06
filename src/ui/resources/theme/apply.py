"""Light/dark theme for the application."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication
from src.ui.resources.theme.colors import DARK, LIGHT

_HERE = Path(__file__).parent
_ICONS_DIR = (_HERE.parent / "icons").as_posix()

_dark_active: bool = False


def is_dark() -> bool:
    """Return the theme that was last applied (not the OS palette)."""
    return _dark_active

def apply_theme(app: QApplication, *, dark: bool | None = None) -> None:
    """Apply light or dark theme to the application.

    Pass dark=True to force dark, dark=False to force light.
    Pass dark=None (default) to follow the OS.
    """
    if dark is None:
        dark = app.palette().color(QPalette.ColorRole.Window).lightness() < 128

    global _dark_active
    _dark_active = dark
    tokens = DARK if dark else LIGHT
    app.setStyle("Fusion")
    qss = (_HERE / ("dark.qss" if dark else "light.qss")).read_text(encoding="utf-8")
    # Replace longer names first so e.g. @bg_hover_tint isn't clobbered by @bg_hover.
    for name, value in sorted(tokens.items(), key=lambda kv: -len(kv[0])):
        qss = qss.replace(f"@{name}", value)
    qss = qss.replace("@icons_dir", _ICONS_DIR)
    app.setStyleSheet("")
    app.setStyleSheet(qss)
