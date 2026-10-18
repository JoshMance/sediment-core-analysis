"""WorkspacePresenter — reacts to WorkspaceState and manages panel lifecycle."""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from src.application import AppController
from src.application.workspace_state import WorkspaceEntry, WorkspaceState
from src.application.services.panel_registry import PANEL_TYPE_CONFIG
from src.domain.store import Store
from src.ui.views.shell.workspace import WorkspaceView


class WorkspacePresenter(QObject):
    """Owns the lifecycle of all open panel views and their presenters.

    Listens to WorkspaceState signals to create/destroy panel UI, and keeps
    strong references to both the view and presenter for each open panel to
    prevent garbage collection.
    """

    def __init__(
        self,
        view: WorkspaceView,
        workspace_state: WorkspaceState,
        store: Store,
        controller: AppController,
    ) -> None:
        super().__init__()
        self._view = view
        self._workspace_state = workspace_state
        self._store = store
        self._controller = controller

        # panel_id → (panel_widget, panel_presenter) — keeps both alive
        self._panels: dict[str, tuple[QWidget, QObject]] = {}
        self._panel_types: dict[str, str] = {}  # panel_id → panel_type
        self._panel_targets: dict[str, str | None] = {}  # panel_id → target_entity_id

        workspace_state.panelAdded.connect(self._on_panel_added)
        workspace_state.panelRemoved.connect(self._on_panel_removed)
        workspace_state.panelFocusRequested.connect(self._view.focus_tab)
        view.tabClosed.connect(self._on_tab_closed)
        view.tabChanged.connect(self._on_tab_changed)
        view.entityDropped.connect(self._on_entity_dropped)
        store.entityUpdated.connect(self._on_entity_updated)

    # ── WorkspaceState → View ─────────────────────────────────

    def _on_panel_added(self, entry: WorkspaceEntry) -> None:
        panel_view, panel_presenter = self._create_panel(entry)
        self._panels[entry.panel_id] = (panel_view, panel_presenter)
        self._panel_types[entry.panel_id] = entry.panel_type
        self._panel_targets[entry.panel_id] = entry.target_entity_id

        if entry.panel_type == "CoreStudioPanel":
            core_id = entry.target_entity_id
            if core_id is None:
                title = "Core Studio"
            else:
                entity = self._store.get(core_id)
                core_name = getattr(entity, "name", core_id)
                title = f"{core_name} Studio"
        elif entry.panel_type == "FenceDiagramPanel":
            title = "Fence Diagram"
        else:
            if entry.target_entity_id is None:
                raise ValueError(
                    f"{entry.panel_type} requires target_entity_id for panel '{entry.panel_id}'."
                )
            target_id = entry.target_entity_id
            entity = self._store.get(target_id)
            title = getattr(entity, "name", target_id)
        self._view.add_tab(panel_view, title, entry.panel_id)

    def _on_panel_removed(self, panel_id: str) -> None:
        self._panels.pop(panel_id, None)
        self._panel_types.pop(panel_id, None)
        self._panel_targets.pop(panel_id, None)
        self._view.remove_tab(panel_id)

    # ── View → WorkspaceState ─────────────────────────────────

    def _on_entity_updated(self, entity_id: str, _entity_type: str) -> None:
        """Store says an entity was updated — refresh the tab title if open."""
        entity = self._store.get(entity_id)
        if entity is None:
            return
        for panel_id, target_id in self._panel_targets.items():
            if target_id != entity_id:
                continue
            panel_type = self._panel_types.get(panel_id)
            if panel_type == "CoreStudioPanel":
                self._view.rename_tab(panel_id, f"{getattr(entity, 'name', entity_id)} Studio")
            else:
                self._view.rename_tab(panel_id, getattr(entity, "name", entity_id))

    def _on_tab_changed(self, panel_id: str) -> None:
        """Active workspace tab changed — sync ribbon and active-panel state."""
        self._workspace_state.set_active_panel(panel_id or None)
        if not panel_id:
            self._controller.set_ribbon_tab("Home")
            return
        panel_type = self._panel_types.get(panel_id, "")
        config = PANEL_TYPE_CONFIG.get(panel_type)
        tab_name = config.ribbon_tab if config else "Home"
        self._controller.set_ribbon_tab(tab_name)

    def _on_tab_closed(self, panel_id: str) -> None:
        self._panels.pop(panel_id, None)
        self._panel_types.pop(panel_id, None)
        self._panel_targets.pop(panel_id, None)
        self._workspace_state.close(panel_id)

    def _on_entity_dropped(self, entity_id: str) -> None:
        """User dropped an entity onto the workspace.
        
        By default, opens the entity in the workspace (image editor).
        Lanes in active fence diagram panel will intercept drops directly.
        """
        # Default behavior: open in image editor
        self._controller.open_in_workspace(entity_id)

    # ── Panel factory ─────────────────────────────────────────

    def _create_panel(self, entry: WorkspaceEntry) -> tuple[QWidget, QObject]:
        config = PANEL_TYPE_CONFIG.get(entry.panel_type)
        if config is None:
            raise ValueError(
                f"No panel config registered for panel type '{entry.panel_type}'."
            )
        return config.factory(entry, self._store, self._controller)
