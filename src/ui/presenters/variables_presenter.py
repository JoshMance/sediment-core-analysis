"""
VariablesPresenter - connects VariablesList view to Store and AppController

Follows MVP pattern where Presenter:
- Handles View events → calls AppController methods
- Handles Store signals → updates the View's display
- Can read Store directly via its public API when needed
"""
from __future__ import annotations

from PySide6.QtCore import QObject

from src.ui.views.shell.variables_list import VariablesList
from src.domain.store import Store
from src.application import AppController


class VariablesPresenter(QObject):
    def __init__(self, view: VariablesList, store: Store, controller: AppController):
        super().__init__()
        self.view = view
        self.store = store
        self.controller = controller

        # ── Listen to Store signals ─────────────────────────
        self.store.entityAdded.connect(self._on_entity_added)
        self.store.entityRemoved.connect(self._on_entity_removed)

        # ── Listen to View signals ──────────────────────────
        self.view.deleteRequested.connect(self._on_delete_requested)
        self.view.renameRequested.connect(self._on_rename_requested)
        self.view.entityOpenRequested.connect(self._on_entity_open_requested)

        # ── Listen to Store signals ─────────────────────────
        self.store.entityUpdated.connect(self._on_entity_updated)

    # ── Store → View ────────────────────────────────────────

    def _on_entity_added(self, entity_id: str, entity_type: str):
        """Store says an entity was added - read it and tell the view."""
        entity = self.store.get(entity_id)
        name = getattr(entity, "name", str(entity_id))
        display_type = entity_type.removesuffix("Entity")
        self.view.add_row(entity_id, name, display_type)

    def _on_entity_removed(self, entity_id: str, entity_type: str):
        """Store says an entity was removed — tell the view."""
        self.view.remove_row(entity_id)

    # ── View → AppController ──────────────────────────────

    def _on_entity_updated(self, entity_id: str, _entity_type: str):
        """Store says an entity was updated — refresh the row name."""
        entity = self.store.get(entity_id)
        if entity is not None:
            self.view.update_row_name(entity_id, getattr(entity, "name", str(entity_id)))

    def _on_delete_requested(self, entity_id: str):
        """User clicked Delete — route to AppController."""
        self.controller.delete_entity(entity_id)

    def _on_rename_requested(self, entity_id: str, new_name: str):
        """User confirmed a rename — route to AppController."""
        self.controller.rename_entity(entity_id, new_name)

    def _on_entity_open_requested(self, entity_id: str):
        """User double-clicked a row — open the entity in the workspace."""
        self.controller.open_in_workspace(entity_id)
