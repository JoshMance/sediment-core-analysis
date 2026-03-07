"""VariablesList - shows loaded entities and allows deletion.

Pure view component. Knows nothing about Store, AppController, or entity
internals. Displays rows of (name, type) and emits raw UI signals.
The Presenter tells it what to show via add_row / remove_row.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Signal


class VariablesList(QWidget):
    """Displays loaded entities and lets the user delete them."""

    # ── Signals (raw UI events only) ────────────────────────
    deleteRequested = Signal(str)   # entity_id when user clicks Delete
    entitySelected = Signal(str)    # entity_id when user clicks a row

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

        # ── Delete button ───────────────────────────────────
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete_clicked)

        # ── Layout ──────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._delete_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)
        layout.addLayout(btn_layout)

    # ── Public interface (called by Presenter) ──────────────

    def add_row(self, entity_id: str, name: str, entity_type: str) -> None:
        """Add a row to the list."""
        item = QTreeWidgetItem([name, entity_type, entity_id])
        self._tree.addTopLevelItem(item)

    def remove_row(self, entity_id: str) -> None:
        """Remove the row with the given entity id."""
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item and item.text(2) == entity_id:
                self._tree.takeTopLevelItem(i)
                break
        # Disable delete if nothing left selected
        if self._tree.currentItem() is None:
            self._delete_btn.setEnabled(False)

    def clear_rows(self) -> None:
        """Remove all rows."""
        self._tree.clear()
        self._delete_btn.setEnabled(False)

    def row_count(self) -> int:
        """Return the number of rows."""
        return self._tree.topLevelItemCount()

    # ── Internal slots ──────────────────────────────────────

    def _on_selection_changed(self, current: QTreeWidgetItem | None, _previous):
        """Enable/disable delete button based on selection."""
        has_selection = current is not None
        self._delete_btn.setEnabled(has_selection)
        if has_selection:
            entity_id = current.text(2)
            self.entitySelected.emit(entity_id)

    def _on_delete_clicked(self):
        """Emit deleteRequested with the selected entity's id."""
        current = self._tree.currentItem()
        if current:
            entity_id = current.text(2)
            self.deleteRequested.emit(entity_id)
