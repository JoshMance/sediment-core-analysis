"""CsvPanel — view for displaying and editing a CsvEntity's tabular data.

Two classes are defined here:

    DataFrameTableModel  — private Qt MVC adapter (QAbstractTableModel).
                           Bridges a pandas DataFrame to a QTableView.
                           Never imported outside this module.

    CsvPanel             — the public QWidget view.
                           Emits signals for all user edits; contains
                           no domain or application logic.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHeaderView,
    QInputDialog,
    QMenu,
    QTableView,
    QVBoxLayout,
    QWidget,
)


# ── Private Qt model ──────────────────────────────────────────────────────────

class _DataFrameTableModel(QAbstractTableModel):
    """Qt table model adapter for a pandas DataFrame.

    Supports in-place cell editing. Column structure changes (rename, retype)
    are handled externally by the presenter — they trigger a full model reset.
    """

    def __init__(self, df: pd.DataFrame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._df = df

    # ── Qt overrides ─────────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        value = self._df.iloc[index.row(), index.column()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if pd.isna(value):
                return "" if role == Qt.ItemDataRole.DisplayRole else None
            return str(value) if role == Qt.ItemDataRole.DisplayRole else value
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        self._df.iloc[index.row(), index.column()] = value
        self.dataChanged.emit(index, index, [role])
        return True

    # ── Public helpers called by CsvPanel ─────────────────────────

    def replace_dataframe(self, df: pd.DataFrame) -> None:
        """Swap in a new DataFrame and reset the view."""
        self.beginResetModel()
        self._df = df
        self.endResetModel()


# ── Public view ───────────────────────────────────────────────────────────────

_TYPE_OPTIONS: list[str] = ["object", "int64", "float64", "bool"]


class CsvPanel(QWidget):
    """View for a CsvEntity. Displays the DataFrame in an editable table.

    Signals:
        cellEdited(row, col, value): User changed a cell value.
        columnRenamed(old_name, new_name): User renamed a header column.
        columnTypeChangeRequested(col_name, new_type): User requested a type cast.
    """

    cellEdited = Signal(int, int, object)
    columnRenamed = Signal(str, str)
    columnTypeChangeRequested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = _DataFrameTableModel(pd.DataFrame(), self)

        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setDefaultSectionSize(24)
        self._table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

        # Context menu on column header
        self._table.horizontalHeader().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._table.horizontalHeader().customContextMenuRequested.connect(
            self._on_header_context_menu
        )

        # Cell edits
        self._model.dataChanged.connect(self._on_model_data_changed)

    # ── Public API called by presenter ────────────────────────────

    def load_dataframe(
        self,
        df: pd.DataFrame,
        columns: list[str],
        column_types: dict[str, str],
    ) -> None:
        """Replace the displayed DataFrame. Called by presenter on init / refresh."""
        self._model.dataChanged.disconnect(self._on_model_data_changed)
        self._model.replace_dataframe(df)
        self._model.dataChanged.connect(self._on_model_data_changed)

    # ── Internal signal handlers ──────────────────────────────────

    def _on_model_data_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: list[int],
    ) -> None:
        """Translate Qt model edits to our domain-facing cellEdited signal."""
        if Qt.ItemDataRole.EditRole in roles:
            row = top_left.row()
            col = top_left.column()
            value = self._model.data(top_left, Qt.ItemDataRole.EditRole)
            self.cellEdited.emit(row, col, value)

    def _on_header_context_menu(self, pos) -> None:
        """Show rename / change-type options for the clicked column."""
        col_ix = self._table.horizontalHeader().logicalIndexAt(pos)
        if col_ix < 0 or col_ix >= self._model.columnCount():
            return

        col_name = self._model.headerData(
            col_ix, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )

        menu = QMenu(self)

        # Rename action
        rename_action = QAction("Rename column…", self)
        rename_action.triggered.connect(
            lambda: self._rename_column(col_name)
        )
        menu.addAction(rename_action)

        # Change type submenu
        type_menu = QMenu("Change type", self)
        for type_name in _TYPE_OPTIONS:
            action = QAction(type_name, self)
            action.triggered.connect(
                lambda checked=False, t=type_name: self.columnTypeChangeRequested.emit(
                    col_name, t
                )
            )
            type_menu.addAction(action)
        menu.addMenu(type_menu)

        menu.exec(self._table.horizontalHeader().mapToGlobal(pos))

    def _rename_column(self, current_name: str) -> None:
        """Show an input dialog and emit columnRenamed if the user confirms."""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Column",
            "New name:",
            text=current_name,
        )
        if ok and new_name and new_name != current_name:
            self.columnRenamed.emit(current_name, new_name)
