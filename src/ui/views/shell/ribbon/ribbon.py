"""Ribbon -- tabbed toolbar across the top of the window."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from PySide6.QtCore import Qt, Signal

from src.ui.views.shell.ribbon.ribbon_button import RibbonButton
from src.ui.views.shell.ribbon.ribbon_group import RibbonGroup

_ICONS_DIR = Path(__file__).parents[3] / "resources" / "icons"

# Maps button label → icon filename (add entries as icons are provided)
_ICON_MAP: dict[str, str] = {
    "New": "new-session.svg",
    "Open": "open.svg",
    "Save": "save-session.svg",
    "Load Image": "load-image.svg",
    "Load Data": "load-data.svg",
    "Load Map": "load-map.svg",
}


class Ribbon(QWidget):
    """
    Every button click emits ``buttonClicked(button_name)`` so the
    presenter only needs to connect one signal.
    """

    buttonClicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("ribbon")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._tabs = QTabWidget()
        # document mode disabled — Fusion ignores QTabBar background-color with it on

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tabs)

        self.setFixedHeight(150)
        self._build_tabs()

    # -- public API -----------------------------------------------

    def set_button_enabled(self, name: str, enabled: bool) -> None:
        """Enable / disable a button by its label."""
        btn = self._buttons.get(name)
        if btn:
            btn.setEnabled(enabled)

    # -- internals ------------------------------------------------

    def _build_tabs(self) -> None:
        """Assemble all tabs, groups, and buttons."""
        self._buttons: dict[str, RibbonButton] = {}

        # -- Home tab
        home = self._make_tab()
        self._add_group(home, "File", ["New", "Open", "Save"])
        self._add_group(home, "Import", ["Load Image", "Load Data", "Load Map"])
        self._add_group(home, "Edit", ["Undo", "Redo"])
        self._tabs.addTab(home, "Home")

        # -- View tab
        view = self._make_tab()
        self._add_group(view, "Calibrate", ["Calibrate"])
        self._add_group(view, "Core", ["Core Studio"])
        self._tabs.addTab(view, "View")

        # -- Analysis tab
        analysis = self._make_tab()
        self._add_group(analysis, "Core", ["Analyse"])
        self._tabs.addTab(analysis, "Analysis")

        # -- Map tab
        map_tab = self._make_tab()
        self._tabs.addTab(map_tab, "Map")

        # -- Export tab
        export_tab = self._make_tab()
        self._tabs.addTab(export_tab, "Export")

    def _make_tab(self) -> QWidget:
        """Create an empty tab with a left-aligned horizontal layout."""
        tab = QWidget()
        lay = QHBoxLayout(tab)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        lay.addStretch()
        return tab

    def _add_group(self, tab: QWidget, title: str, labels: list[str]) -> None:
        """Add a RibbonGroup with the given buttons to *tab*."""
        group = RibbonGroup(title)
        for label in labels:
            btn = RibbonButton(label)
            icon_path = _ICONS_DIR / _ICON_MAP[label] if label in _ICON_MAP else None
            if icon_path and icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
            btn.clicked.connect(lambda checked=False, name=label: self.buttonClicked.emit(name))
            group.add_button(btn)
            self._buttons[label] = btn
        # insert before the stretch
        lay = tab.layout()
        lay.insertWidget(lay.count() - 1, group)
