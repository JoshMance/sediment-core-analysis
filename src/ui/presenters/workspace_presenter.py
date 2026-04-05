"""WorkspacePresenter — reacts to WorkspaceState and manages panel lifecycle."""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from src.application import AppController
from src.application.workspace_state import WorkspaceEntry, WorkspaceState
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

        # entity_id → (panel_widget, panel_presenter) — keeps both alive
        self._panels: dict[str, tuple[QWidget, QObject]] = {}

        workspace_state.panelAdded.connect(self._on_panel_added)
        workspace_state.panelRemoved.connect(self._on_panel_removed)
        workspace_state.panelFocusRequested.connect(self._view.focus_tab)
        view.tabClosed.connect(self._on_tab_closed)
        view.entityDropped.connect(self._on_entity_dropped)
        store.entityUpdated.connect(self._on_entity_updated)

    # ── WorkspaceState → View ─────────────────────────────────

    def _on_panel_added(self, entry: WorkspaceEntry) -> None:
        panel_view, panel_presenter = self._create_panel(entry)
        self._panels[entry.entity_id] = (panel_view, panel_presenter)

        entity = self._store.get(entry.entity_id)
        title = getattr(entity, "name", entry.entity_id)
        self._view.add_tab(panel_view, title, entry.entity_id)

    def _on_panel_removed(self, entity_id: str) -> None:
        self._panels.pop(entity_id, None)
        self._view.remove_tab(entity_id)

    # ── View → WorkspaceState ─────────────────────────────────

    def _on_entity_updated(self, entity_id: str, _entity_type: str) -> None:
        """Store says an entity was updated — refresh the tab title if open."""
        if entity_id not in self._panels:
            return
        entity = self._store.get(entity_id)
        if entity is not None:
            self._view.rename_tab(entity_id, getattr(entity, "name", entity_id))

    def _on_tab_closed(self, entity_id: str) -> None:
        self._panels.pop(entity_id, None)
        self._workspace_state.close(entity_id)

    def _on_entity_dropped(self, entity_id: str) -> None:
        """User dropped an entity onto the workspace — open it like a double-click."""
        self._controller.open_in_workspace(entity_id)

    # ── Panel factory ─────────────────────────────────────────

    def _create_panel(self, entry: WorkspaceEntry) -> tuple[QWidget, QObject]:
        factory = _PANEL_FACTORIES.get(entry.panel_type)
        if factory is None:
            raise ValueError(
                f"No factory registered for panel type '{entry.panel_type}'."
            )
        return factory(entry, self._store, self._controller)


# ── Factory functions (one per panel type) ────────────────────

def _make_image_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.image_panel import ImagePanel
    from src.ui.presenters.image_panel_presenter import ImagePanelPresenter

    view = ImagePanel()
    presenter = ImagePanelPresenter(view, store, controller, entry.entity_id)
    return view, presenter


def _make_dataset_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.dataset_panel.dataset_panel import DatasetPanel
    from src.ui.presenters.dataset_panel_presenter import DatasetPanelPresenter

    view = DatasetPanel()
    presenter = DatasetPanelPresenter(view, store, controller, entry.entity_id)
    return view, presenter


def _make_core_studio_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.core_studio_panel import CoreStudioPanel
    from src.ui.presenters.core_studio_presenter import CoreStudioPresenter

    view = CoreStudioPanel()
    presenter = CoreStudioPresenter(view, store, controller)
    return view, presenter


_PANEL_FACTORIES: dict[str, object] = {
    "ImagePanel": _make_image_panel,
    "DatasetPanel": _make_dataset_panel,
    "CoreStudioPanel": _make_core_studio_panel,
}
