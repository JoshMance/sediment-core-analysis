"""VariablesList - shows loaded entities and allows deletion.

Pure view component. Knows nothing about Store, AppController, or entity
internals. Displays rows of (name, type) and emits raw UI signals.
The Presenter tells it what to show via add_row / remove_row.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,
    QHeaderView, QMenu, QInputDialog, QLabel, QFileIconProvider,
)
from PySide6.QtCore import Signal, Qt, QFileInfo, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter

ENTITY_MIME_TYPE = "application/x-entity-id"


class VariablesList(QWidget):
    """Displays loaded entities and lets the user delete them."""

    # ── Signals (raw UI events only) ────────────────────────
    deleteRequested = Signal(str)        # entity_id
    renameRequested = Signal(str, str)   # entity_id, new_name
    entitySelected = Signal(str)         # entity_id when user single-clicks a row
    entityOpenRequested = Signal(str)    # entity_id when user double-clicks a row
    openInCoreStudioRequested = Signal(str)  # core entity_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── Tree widget ─────────────────────────────────────
        self._icon_provider = QFileIconProvider()

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(2)
        self._tree.setColumnHidden(1, True)
        self._tree.setRootIsDecorated(True)
        self._tree.setIndentation(12)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._tree.setDragEnabled(True)

        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu_requested)
        self._tree.startDrag = self._start_drag

        # ── Layout ──────────────────────────────────────────
        panel_header = QLabel("Explorer")
        panel_header.setObjectName("panelHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panel_header)
        layout.addWidget(self._tree)

    # ── Public interface (called by Presenter) ──────────────

    def add_row(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        parent_id: str | None = None,
        file_path: str | None = None,
    ) -> None:
        item = QTreeWidgetItem([name, entity_id])
        item.setData(0, Qt.ItemDataRole.UserRole, entity_type)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, name)
        if file_path:
            item.setIcon(0, self._icon_provider.icon(QFileInfo(file_path)))
        else:
            item.setIcon(0, self._icon_provider.icon(QFileIconProvider.IconType.File))
        parent_item = self._find_item(parent_id) if parent_id else None
        if parent_item is not None:
            parent_item.addChild(item)
            parent_item.setExpanded(True)
        else:
            self._tree.addTopLevelItem(item)

    def update_row_name(self, entity_id: str, new_name: str) -> None:
        item = self._find_item(entity_id)
        if item is not None:
            item.setText(0, new_name)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, new_name)

    def remove_row(self, entity_id: str) -> None:
        item = self._find_item(entity_id)
        if item is None:
            return
        # Re-parent children to the tree root before removing
        while item.childCount():
            child = item.takeChild(0)
            self._tree.addTopLevelItem(child)
        parent = item.parent()
        if parent is not None:
            parent.removeChild(item)
        else:
            idx = self._tree.indexOfTopLevelItem(item)
            if idx >= 0:
                self._tree.takeTopLevelItem(idx)

    def clear_rows(self) -> None:
        self._tree.clear()

    def row_count(self) -> int:
        """Total number of items in the tree (all levels)."""
        count = 0
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            count += 1
            iterator += 1
        return count

    # ── Tree search ─────────────────────────────────────────

    def _find_item(self, entity_id: str | None) -> QTreeWidgetItem | None:
        """Find an item anywhere in the tree by entity_id (column 1, hidden)."""
        if entity_id is None:
            return None
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if item.text(1) == entity_id:
                return item
            iterator += 1
        return None

    # ── Drag support ────────────────────────────────────────

    def _start_drag(self, supported_actions) -> None:
        """Initiate a drag carrying the selected entity_id as mime data."""
        item = self._tree.currentItem()
        if item is None:
            return
        entity_id = item.text(1)
        mime = QMimeData()
        mime.setData(ENTITY_MIME_TYPE, entity_id.encode("utf-8"))

        # Semi-opaque snapshot of the row as the drag pixmap.
        rect = self._tree.visualItemRect(item)
        pixmap = self._tree.viewport().grab(rect)
        faded = QPixmap(pixmap.size())
        faded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(faded)
        painter.setOpacity(0.6)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        drag = QDrag(self._tree)
        drag.setMimeData(mime)
        drag.setPixmap(faded)
        drag.setHotSpot(rect.center() - rect.topLeft())
        drag.exec(Qt.DropAction.CopyAction)

    # ── Internal slots ──────────────────────────────────────

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous):
        if current is not None:
            self.entitySelected.emit(current.text(1))

    def _on_item_double_clicked(self, item, _column) -> None:
        self.entityOpenRequested.emit(item.text(1))

    def _on_context_menu_requested(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if item is None:
            return
        entity_id = item.text(1)
        entity_type = item.data(0, Qt.ItemDataRole.UserRole)
        current_name = item.data(0, Qt.ItemDataRole.UserRole + 1) or item.text(0)

        menu = QMenu(self)

        open_in_core_studio_action = None
        if entity_type == "Core":
            open_in_core_studio_action = menu.addAction("Open In Core Studio")
            menu.addSeparator()

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self._tree.viewport().mapToGlobal(pos))

        if open_in_core_studio_action is not None and action == open_in_core_studio_action:
            self.openInCoreStudioRequested.emit(entity_id)

        elif action == rename_action:
            p = Path(current_name)
            stem, suffix = p.stem, p.suffix
            new_stem, ok = QInputDialog.getText(
                self, "Rename", "New name:", text=stem
            )
            if ok and new_stem.strip():
                self.renameRequested.emit(entity_id, new_stem.strip() + suffix)

        elif action == delete_action:
            self.deleteRequested.emit(entity_id)
