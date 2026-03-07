"""
WorkspacePresenter - connects WorkspacePanel view to Store and Controller

Follows MVP pattern where Presenter:
- Handles View events → calls Controller methods
- Handles Store signals → updates the View's display
- Can read Store directly via its public API when needed
"""
from __future__ import annotations

from PySide6.QtCore import QObject

from src.views.panels.workspace_panel import WorkspacePanel
from src.store import Store
from src.controller import Controller


class WorkspacePresenter(QObject):
    def __init__(self, view: WorkspacePanel, store: Store, controller: Controller):
        super().__init__()
        self.view = view
        self.store = store
        self.controller = controller

        # ── Listen to Store signals ─────────────────────────
        self.store.entityAdded.connect(self._on_entity_added)
        self.store.entityRemoved.connect(self._on_entity_removed)

        # ── Listen to View signals ──────────────────────────
        self.view.deleteRequested.connect(self._on_delete_requested)

    # ── Store → View ────────────────────────────────────────

    def _on_entity_added(self, entity_id: str, entity_type: str):
        """Store says an entity was added — read it and tell the view."""
        entity = self.store.get(entity_id)
        name = getattr(entity, "name", str(entity_id))
        self.view.add_row(entity_id, name, entity_type)

    def _on_entity_removed(self, entity_id: str, entity_type: str):
        """Store says an entity was removed — tell the view."""
        self.view.remove_row(entity_id)

    # ── View → Controller ──────────────────────────────────

    def _on_delete_requested(self, entity_id: str):
        """User clicked Delete — route to Controller."""
        self.controller.delete_entity(entity_id)
