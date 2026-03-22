"""DatasetPanelPresenter — connects a DatasetPanel view to the Store and AppController."""
from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QObject

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.dataset_panel.dataset_panel import DatasetPanel


class DatasetPanelPresenter(QObject):
    """Wires a DatasetPanel to its DatasetEntity and the AppController.

    Created by WorkspacePresenter at the time the panel tab is opened.
    Lifetime is owned by WorkspacePresenter's internal dict.
    """

    def __init__(
        self,
        view: DatasetPanel,
        store: Store,
        controller: AppController,
        entity_id: str,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._entity_id = entity_id

        self._load_data()

        # View → AppController
        view.cellEdited.connect(self._on_cell_edited)
        view.columnRenamed.connect(self._on_column_renamed)
        view.columnTypeChangeRequested.connect(self._on_column_type_change_requested)

        # Store → View  (refresh on any mutation to this entity)
        store.entityUpdated.connect(self._on_entity_updated)

    # ── Store → View ─────────────────────────────────────────────

    def _load_data(self) -> None:
        """Fetch the entity's DataFrame, apply display types, and push to the view."""
        entity = self._store.get(self._entity_id)
        if entity is None or entity.data is None:
            return
        display_df = _apply_display_types(entity.data, entity.column_types)
        self._view.load_dataframe(display_df, entity.columns, entity.column_types)

    def _on_entity_updated(self, entity_id: str, entity_type: str) -> None:
        """Store says something changed — refresh if it's our entity."""
        if entity_id == self._entity_id:
            self._load_data()

    # ── View → AppController ──────────────────────────────────────

    def _on_cell_edited(self, row: int, col: int, value: object) -> None:
        self._controller.update_dataset_cell(self._entity_id, row, col, value)

    def _on_column_renamed(self, old_name: str, new_name: str) -> None:
        self._controller.rename_dataset_column(self._entity_id, old_name, new_name)

    def _on_column_type_change_requested(self, col_name: str, new_type: str) -> None:
        self._controller.change_dataset_column_type(self._entity_id, col_name, new_type)


# ── Display helpers ───────────────────────────────────────────────────────────

def _apply_display_types(
    df: pd.DataFrame,
    column_types: dict[str, str],
) -> pd.DataFrame:
    """Return a copy of *df* with columns cast according to *column_types*.

    The original DataFrame is never modified — this is purely a display
    transformation. Coercion failures produce NaN/NaT rather than raising.
    """
    out = df.copy()
    for col, label in column_types.items():
        if col not in out.columns:
            continue
        if label == "Number":
            if not pd.api.types.is_numeric_dtype(out[col]):
                out[col] = pd.to_numeric(out[col], errors="coerce")
        elif label == "Date":
            out[col] = pd.to_datetime(out[col], errors="coerce")
        # "Text" — leave as-is; raw strings are already displayable
    return out
