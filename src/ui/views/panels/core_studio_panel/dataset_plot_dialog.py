"""DatasetPlotDialog — picker for selecting dataset columns to display as plots.

A modal dialog that shows all datasets in the Store as a tree.  Each dataset
with a designated depth column shows its numeric columns as checkboxes.
Datasets without a depth column are shown greyed-out with a tooltip explaining
what the user must do first.

The dialog does NOT touch the Store directly — it receives the data it needs
at construction time and emits ``plotsSelected`` with the confirmed selection.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DatasetPlotDialog(QDialog):
    """Modal dialog for selecting which dataset columns to plot in Core Studio.

    Args:
        datasets: Sequence of dataset descriptors — each a dict with keys:
            ``id`` (str), ``name`` (str), ``depth_column`` (str | None),
            ``columns`` (list[str]), ``column_types`` (dict[str, str]).
        active_plots: Currently active plots as list of
            ``{'dataset_id': str, 'column_name': str}`` dicts.
            These columns will be pre-checked.
        parent: Optional parent widget.

    Signals:
        plotsSelected(list[dict]): Emitted on Accept with the full new list of
            ``{'dataset_id': str, 'column_name': str}`` dicts.
    """

    plotsSelected = Signal(list)

    def __init__(
        self,
        datasets: list[dict],
        active_plots: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Data Plots")
        self.setMinimumSize(420, 360)

        # Build a quick lookup for active plots
        active_set: set[tuple[str, str]] = {
            (p["dataset_id"], p["column_name"]) for p in active_plots
        }

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)

        self._checkboxes: list[tuple[str, str, QTreeWidgetItem]] = []  # (dataset_id, col_name, item)

        if not datasets:
            placeholder = QTreeWidgetItem(self._tree, ["No datasets loaded."])
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        else:
            for ds in datasets:
                ds_id: str = ds["id"]
                ds_name: str = ds["name"]
                depth_col: str | None = ds.get("depth_column")
                columns: list[str] = ds.get("columns", [])
                column_types: dict[str, str] = ds.get("column_types", {})

                # Dataset root item
                root_label = ds_name
                if depth_col:
                    root_label += f"  [depth: {depth_col}]"
                ds_item = QTreeWidgetItem(self._tree, [root_label])
                ds_item.setFlags(Qt.ItemFlag.ItemIsEnabled)

                if depth_col is None:
                    ds_item.setDisabled(True)
                    ds_item.setToolTip(
                        0,
                        "Set a depth column in the Dataset panel first "
                        "(right-click a column header \u2192 Set as depth column).",
                    )
                    continue

                # Numeric columns as checkbox children (exclude the depth column itself)
                numeric_cols = [
                    c for c in columns
                    if c != depth_col and column_types.get(c) == "Number"
                ]
                if not numeric_cols:
                    no_col_item = QTreeWidgetItem(ds_item, ["(no numeric columns)"])
                    no_col_item.setFlags(Qt.ItemFlag.NoItemFlags)
                    no_col_item.setDisabled(True)
                    continue

                for col in numeric_cols:
                    col_item = QTreeWidgetItem(ds_item, [col])
                    col_item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    state = (
                        Qt.CheckState.Checked
                        if (ds_id, col) in active_set
                        else Qt.CheckState.Unchecked
                    )
                    col_item.setCheckState(0, state)
                    self._checkboxes.append((ds_id, col, col_item))

        self._tree.expandAll()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select columns to display as depth-aligned plots:"))
        layout.addWidget(self._tree, 1)
        layout.addWidget(buttons)

    # ── Private ───────────────────────────────────────────────────────────────

    def _on_accept(self) -> None:
        selected: list[dict] = [
            {"dataset_id": ds_id, "column_name": col}
            for ds_id, col, item in self._checkboxes
            if item.checkState(0) == Qt.CheckState.Checked
        ]
        self.plotsSelected.emit(selected)
        self.accept()
