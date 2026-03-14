"""CsvPanelPresenter — connects a CsvPanel view to the Store and AppController."""
from __future__ import annotations

from PySide6.QtCore import QObject

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.csv_panel.csv_panel import CsvPanel


class CsvPanelPresenter(QObject):
    """Wires a CsvPanel to its CsvEntity and the AppController.

    Created by WorkspacePresenter at the time the panel tab is opened.
    Lifetime is owned by WorkspacePresenter's internal dict.
    """

    def __init__(
        self,
        view: CsvPanel,
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
        """Fetch the entity's DataFrame and push it to the view."""
        entity = self._store.get(self._entity_id)
        if entity is None or entity.data is None:
            return
        self._view.load_dataframe(entity.data, entity.columns, entity.column_types)

    def _on_entity_updated(self, entity_id: str, entity_type: str) -> None:
        """Store says something changed — refresh if it's our entity."""
        if entity_id == self._entity_id:
            self._load_data()

    # ── View → AppController ──────────────────────────────────────

    def _on_cell_edited(self, row: int, col: int, value: object) -> None:
        self._controller.update_csv_cell(self._entity_id, row, col, value)

    def _on_column_renamed(self, old_name: str, new_name: str) -> None:
        self._controller.rename_csv_column(self._entity_id, old_name, new_name)

    def _on_column_type_change_requested(self, col_name: str, new_type: str) -> None:
        self._controller.change_csv_column_type(self._entity_id, col_name, new_type)
