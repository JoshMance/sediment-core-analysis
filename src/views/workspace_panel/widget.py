from PySide6.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QAbstractItemView)
from PySide6.QtCore import QSize, Qt
from typing import Any, Callable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .signals import WorkspacePanelSignals


class WorkspacePanel(QWidget):
    """Main widget displaying workspace items in a table.
    
    Args:
        parent: Parent widget
        columns: List of column definitions, each with 'name' and optional 'resize' ('stretch' or 'fit')
        row_formatter: Function that takes an item and returns a list of strings for each column
    """

    DEFAULT_COLUMNS = [
        {'name': 'Name', 'resize': 'stretch'},
        {'name': 'Type', 'resize': 'fit'},
        {'name': 'Size', 'resize': 'stretch'},
    ]

    def __init__(
        self,
        parent: QWidget | None = None,
        columns: list[dict] | None = None,
        row_formatter: Callable[[Any], list[str]] | None = None
    ) -> None:
        super().__init__(parent)

        # Signals
        self.signals = WorkspacePanelSignals()

        # Internal item storage
        self._items: list = []

        # Column definitions and row formatter
        self._columns = columns or self.DEFAULT_COLUMNS
        self._row_formatter = row_formatter or self._default_row_formatter

        # Table widget
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._columns))
        self._table.setHorizontalHeaderLabels([col['name'] for col in self._columns])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # Set column resize modes from model
        header = self._table.horizontalHeader()
        for i, col in enumerate(self._columns):
            if col.get('resize') == 'fit':
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Connect signals
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.cellDoubleClicked.connect(self._on_double_clicked)

        # Toolbar
        self.toolbar = self._create_toolbar()

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self._table)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with workspace controls."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setToolTip("Remove selected item")
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setEnabled(False)
        toolbar.addWidget(self.remove_btn)

        return toolbar

    def _default_row_formatter(self, item: Any) -> list[str]:
        """Default formatter - uses item's name attribute or str()."""
        name = getattr(item, 'name', str(item))
        type_name = type(item).__name__.lower()
        size = "—"
        if hasattr(item, 'shape') and item.shape is not None:
            h, w = item.shape[:2]
            size = f"{w}x{h} px"
        return [name, type_name, size]

    def _refresh_table(self) -> None:
        """Refresh the table to reflect current items."""
        self._table.setRowCount(len(self._items))
        num_cols = len(self._columns)
        for row, item in enumerate(self._items):
            row_data = self._row_formatter(item)
            for col, value in enumerate(row_data):
                cell = QTableWidgetItem(value)
                # Determine alignment based on column position
                # Left columns -> left aligned, right columns -> right aligned
                if num_cols == 1:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif col == 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                elif col == num_cols - 1:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, cell)

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self.get_selected_item()
        self.remove_btn.setEnabled(selected is not None)
        if selected:
            self.signals.itemSelected.emit(selected)

    def _on_double_clicked(self, row: int, column: int) -> None:
        """Handle double click on table row."""
        if 0 <= row < len(self._items):
            self.signals.itemDoubleClicked.emit(self._items[row])

    def _on_remove_clicked(self) -> None:
        """Remove the selected item."""
        selected = self.get_selected_item()
        if selected:
            self.remove_item(selected)

    def add_item(self, item: Any) -> None:
        """Add an item to the workspace."""
        self._items.append(item)
        self._refresh_table()

    def remove_item(self, item: Any) -> None:
        """Remove an item from the workspace."""
        if item in self._items:
            self._items.remove(item)
            self._refresh_table()
            self.signals.itemRemoved.emit(item)

    def get_items(self) -> list[Any]:
        """Get all items in the workspace."""
        return list(self._items)

    def get_selected_item(self) -> Any | None:
        """Get the currently selected item."""
        selected_rows = self._table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self._items):
                return self._items[row]
        return None

    def clear(self) -> None:
        """Remove all items from the workspace."""
        self._items.clear()
        self._refresh_table()
