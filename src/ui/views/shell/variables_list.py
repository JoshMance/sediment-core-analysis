"""VariablesList - shows loaded entities and allows deletion.

Pure view component. Knows nothing about Store, AppController, or entity
internals. Displays rows of (name, type) and emits raw UI signals.
The Presenter tells it what to show via add_row / remove_row.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QMenu, QInputDialog, QLabel,
)
from PySide6.QtCore import Signal, Qt


class VariablesList(QWidget):
    """Displays loaded entities and lets the user delete them."""

    # ── Signals (raw UI events only) ────────────────────────
    deleteRequested = Signal(str)        # entity_id
    renameRequested = Signal(str, str)   # entity_id, new_name
    entitySelected = Signal(str)         # entity_id when user single-clicks a row
    entityOpenRequested = Signal(str)    # entity_id when user double-clicks a row

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── Tree widget ─────────────────────────────────────
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Name", "Type"])
        self._tree.setColumnCount(3)
        self._tree.setColumnHidden(2, True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu_requested)

        # ── Layout ──────────────────────────────────────────
        panel_header = QLabel("Variables")
        panel_header.setObjectName("panelHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panel_header)
        layout.addWidget(self._tree)

    # ── Public interface (called by Presenter) ──────────────

    def add_row(self, entity_id: str, name: str, entity_type: str) -> None:
        item = QTreeWidgetItem([name, entity_type, entity_id])
        self._tree.addTopLevelItem(item)

    def update_row_name(self, entity_id: str, new_name: str) -> None:
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item and item.text(2) == entity_id:
                item.setText(0, new_name)
                break

    def remove_row(self, entity_id: str) -> None:
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item and item.text(2) == entity_id:
                self._tree.takeTopLevelItem(i)
                break

    def clear_rows(self) -> None:
        self._tree.clear()

    def row_count(self) -> int:
        return self._tree.topLevelItemCount()

    # ── Internal slots ──────────────────────────────────────

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous):
        if current is not None:
            self.entitySelected.emit(current.text(2))

    def _on_item_double_clicked(self, item, _column) -> None:
        self.entityOpenRequested.emit(item.text(2))

    def _on_context_menu_requested(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None:
            return
        entity_id = item.text(2)
        current_name = item.text(0)

        menu = QMenu(self)

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self._tree.viewport().mapToGlobal(pos))

        if action == rename_action:
            p = Path(current_name)
            stem, suffix = p.stem, p.suffix
            new_stem, ok = QInputDialog.getText(
                self, "Rename", "New name:", text=stem
            )
            if ok and new_stem.strip():
                self.renameRequested.emit(entity_id, new_stem.strip() + suffix)

        elif action == delete_action:
            self.deleteRequested.emit(entity_id)
