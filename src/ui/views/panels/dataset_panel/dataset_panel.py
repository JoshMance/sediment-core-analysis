"""DatasetPanel — view for displaying and editing a DatasetEntity's tabular data.

Two classes are defined here:

    DataFrameTableModel  — private Qt MVC adapter (QAbstractTableModel).
                           Bridges a pandas DataFrame to a QTableView.
                           Never imported outside this module.

    DatasetPanel         — the public QWidget view.
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
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QInputDialog,
    QMenu,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


# ── Constants ────────────────────────────────────────────

_DEPTH_SUFFIX = "  ▼ depth"

# ── Cell value validation ────────────────────────────────────────────────────

class _InvalidType:
    """Sentinel returned by _parse_cell_value when input is rejected."""

_INVALID = _InvalidType()


def _parse_cell_value(value: Any, col_type: str) -> Any:
    """Validate and coerce a raw edit value against the declared column type.

    Returns the parsed value on success, or _INVALID if the input is
    not representable as that type (which causes the edit to be rejected).
    Empty string is always treated as NaN / None.
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if col_type == "Text":
        return str(value)
    if col_type == "Number":
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return _INVALID
    if col_type == "Date":
        parsed = pd.to_datetime(value, errors="coerce")
        return None if pd.isna(parsed) else parsed
    return value


# ── Private Qt model ──────────────────────────────────────────────────────────

class _DataFrameTableModel(QAbstractTableModel):
    """Qt table model adapter for a pandas DataFrame.

    Supports in-place cell editing. Column structure changes (rename, retype)
    are handled externally by the presenter — they trigger a full model reset.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        column_types: dict[str, str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._df = df
        self._column_types: dict[str, str] = column_types or {}
        self._depth_column: str | None = None

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
                return ""
            return str(value)
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
            col = str(self._df.columns[section])
            if col == self._depth_column:
                return f"{col}{_DEPTH_SUFFIX}"
            return col
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
        col_name = str(self._df.columns[index.column()])
        col_type = self._column_types.get(col_name, "Text")
        parsed = _parse_cell_value(value, col_type)
        if parsed is _INVALID:
            return False  # reject the edit; Qt restores the old value
        existing = self._df.iloc[index.row(), index.column()]
        both_null = (parsed is None) and pd.isna(existing)
        if both_null or (parsed == existing):
            return True  # nothing changed — don't propagate
        self._df.iloc[index.row(), index.column()] = parsed
        self.dataChanged.emit(index, index, [role])
        return True

    # ── Public helpers called by DatasetPanel ─────────────────────

    def replace_dataframe(
        self, df: pd.DataFrame, column_types: dict[str, str] | None = None
    ) -> None:
        """Swap in a new DataFrame and reset the view."""
        self.beginResetModel()
        self._df = df
        if column_types is not None:
            self._column_types = column_types
        self.endResetModel()

    def set_depth_column(self, col_name: str | None) -> None:
        """Mark *col_name* as the depth column (updates header display)."""
        self._depth_column = col_name
        self.headerDataChanged.emit(
            Qt.Orientation.Horizontal, 0, max(0, len(self._df.columns) - 1)
        )


# ── Public view ───────────────────────────────────────────────────────────────

_TYPE_OPTIONS: list[str] = ["Text", "Number", "Date"]


class DatasetPanel(QWidget):
    """View for a DatasetEntity. Displays the DataFrame in an editable table.

    Signals:
        cellEdited(row, col, value): User changed a cell value.
        columnRenamed(old_name, new_name): User renamed a header column.
        columnTypeChangeRequested(col_name, new_type): User requested a type cast.
    """

    cellEdited = Signal(int, int, object)
    columnRenamed = Signal(str, str)
    columnTypeChangeRequested = Signal(str, str)
    depthColumnSetRequested = Signal(str)  # col_name
    addColumnRequested = Signal()
    removeColumnRequested = Signal(str)    # col_name
    addRowRequested = Signal()
    removeRowRequested = Signal(int)       # row index
    pasteRequested = Signal(int, int, list)  # start_row, start_col, list[list[str]]
    selectionChanged = Signal(int, int)  # row, col (0-based)
    columnSelected = Signal(int)           # col (0-based), entire column clicked

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = _DataFrameTableModel(pd.DataFrame(), self)

        self._toolbar = self._build_toolbar()

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
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._table)

        # Context menu on column header
        self._table.horizontalHeader().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._table.horizontalHeader().customContextMenuRequested.connect(
            self._on_header_context_menu
        )

        # Context menu on row header (vertical)
        self._table.verticalHeader().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._table.verticalHeader().customContextMenuRequested.connect(
            self._on_row_context_menu
        )

        # Cell edits
        self._model.dataChanged.connect(self._on_model_data_changed)

        # Selection / hover
        self._table.viewport().setMouseTracking(True)
        self._table.selectionModel().currentChanged.connect(self._on_current_changed)
        self._table.entered.connect(self._on_item_entered)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_section_clicked)

        # Paste shortcut (Ctrl+V)
        paste_action = QAction(self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        paste_action.triggered.connect(self._on_paste)
        self.addAction(paste_action)

    # ── Public API called by presenter ────────────────────────────

    def load_dataframe(
        self,
        df: pd.DataFrame,
        columns: list[str],
        column_types: dict[str, str],
        depth_column: str | None = None,
    ) -> None:
        """Replace the displayed DataFrame. Called by presenter on init / refresh."""
        self._model.dataChanged.disconnect(self._on_model_data_changed)
        self._model.replace_dataframe(df, column_types)
        self._model.set_depth_column(depth_column)
        self._model.dataChanged.connect(self._on_model_data_changed)
    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)
        add_col = QAction("+ Column", tb)
        add_col.setToolTip("Append a new column")
        add_col.triggered.connect(self.addColumnRequested)
        tb.addAction(add_col)
        add_row = QAction("+ Row", tb)
        add_row.setToolTip("Append a blank row")
        add_row.triggered.connect(self.addRowRequested)
        tb.addAction(add_row)
        return tb
    # ── Internal signal handlers ──────────────────────────────────

    def _on_current_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        """Emit selectionChanged whenever the active cell moves (click / keyboard)."""
        if current.isValid():
            self.selectionChanged.emit(current.row(), current.column())

    def _on_item_entered(self, index: QModelIndex) -> None:
        """Emit selectionChanged when the mouse hovers over a cell."""
        if index.isValid():
            self.selectionChanged.emit(index.row(), index.column())

    def _on_header_section_clicked(self, col: int) -> None:
        """Emit columnSelected when a column header is clicked."""
        self.columnSelected.emit(col)

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
        """Show rename / change-type / depth / remove options for the clicked column."""
        col_ix = self._table.horizontalHeader().logicalIndexAt(pos)
        if col_ix < 0 or col_ix >= self._model.columnCount():
            return

        col_name = self._model.headerData(
            col_ix, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        # Strip the depth indicator suffix to get the real column name
        if col_name and col_name.endswith(_DEPTH_SUFFIX):
            col_name = col_name[: -len(_DEPTH_SUFFIX)]

        menu = QMenu(self)

        # Rename action
        rename_action = QAction("Rename column…", self)
        rename_action.triggered.connect(
            lambda: self._rename_column(col_name)
        )
        menu.addAction(rename_action)

        # Set as depth column action
        set_depth_action = QAction("Set as depth column (mm)", self)
        set_depth_action.triggered.connect(
            lambda: self.depthColumnSetRequested.emit(col_name)
        )
        menu.addAction(set_depth_action)

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

        menu.addSeparator()
        remove_col_action = QAction("Remove column", self)
        remove_col_action.triggered.connect(
            lambda: self.removeColumnRequested.emit(col_name)
        )
        menu.addAction(remove_col_action)

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

    def _on_row_context_menu(self, pos) -> None:
        """Show 'Delete row' for the right-clicked row number."""
        row_ix = self._table.verticalHeader().logicalIndexAt(pos)
        if row_ix < 0 or row_ix >= self._model.rowCount():
            return
        menu = QMenu(self)
        delete_action = QAction("Delete row", self)
        delete_action.triggered.connect(lambda: self.removeRowRequested.emit(row_ix))
        menu.addAction(delete_action)
        menu.exec(self._table.verticalHeader().mapToGlobal(pos))

    def _on_paste(self) -> None:
        """Parse clipboard as TSV and emit pasteRequested with the 2-D cell block."""
        text = QApplication.clipboard().text()
        if not text:
            return

        # Normalise line endings, strip trailing blank line that Excel adds
        lines = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")
        rows: list[list[str]] = [line.split("\t") for line in lines]
        if not rows:
            return

        # Start from the current selection (top-left corner), fall back to (0, 0)
        idx = self._table.currentIndex()
        start_row = idx.row() if idx.isValid() else 0
        start_col = idx.column() if idx.isValid() else 0
        # If table is empty (no columns yet) anchor at origin
        if start_row < 0:
            start_row = 0
        if start_col < 0:
            start_col = 0

        self.pasteRequested.emit(start_row, start_col, rows)
