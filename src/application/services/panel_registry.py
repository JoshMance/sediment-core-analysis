"""Panel registry — centralized mapping of entities, panels, factories, and UI configuration.

Single source of truth for:
- Entity types → Panel types
- Panel types → ID prefixes and factories
- Panel types → Ribbon tabs
- All panel factory functions

To add a new panel type:
1. Add entries to ENTITY_TYPE_TO_PANEL_TYPE, PANEL_TYPE_CONFIG
2. Define a factory function _make_*_panel()
3. That's it — everything else derives from these two sources.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject

from src.application import AppController
from src.application.workspace_state import WorkspaceEntry
from src.domain.store import Store


# ── Entity → Panel type mapping ────────────────────────────────────────────

ENTITY_TYPE_TO_PANEL_TYPE: dict[str, str] = {
    "DatasetEntity": "DatasetPanel",
    "CoreEntity": "CoreImagePanel",
}


# ── Panel type configuration ───────────────────────────────────────────────

class PanelConfig:
    """Configuration for a single panel type."""
    def __init__(
        self,
        panel_type: str,
        id_prefix: str,
        factory: Callable,
        ribbon_tab: str = "Home",
    ):
        self.panel_type = panel_type
        self.id_prefix = id_prefix
        self.factory = factory
        self.ribbon_tab = ribbon_tab


# ── Factory functions (one per panel type) ────────────────────────────────

def _make_core_image_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.core_image_panel import CoreImagePanel
    from src.ui.presenters.core_image_panel_presenter import CoreImagePanelPresenter

    if entry.target_entity_id is None:
        raise ValueError("CoreImagePanel requires target_entity_id")

    view = CoreImagePanel()
    presenter = CoreImagePanelPresenter(view, store, controller, entry.target_entity_id)
    return view, presenter


def _make_dataset_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.dataset_panel.dataset_panel import DatasetPanel
    from src.ui.presenters.dataset_panel_presenter import DatasetPanelPresenter

    if entry.target_entity_id is None:
        raise ValueError("DatasetPanel requires target_entity_id")

    view = DatasetPanel()
    presenter = DatasetPanelPresenter(view, store, controller, entry.target_entity_id)
    return view, presenter


def _make_core_studio_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.core_studio_panel import CoreStudioPanel
    from src.ui.presenters.core_studio_presenter import CoreStudioPresenter

    view = CoreStudioPanel()
    presenter = CoreStudioPresenter(view, store, controller, entry.target_entity_id)
    return view, presenter


def _make_fence_diagram_panel(
    entry: WorkspaceEntry,
    store: Store,
    controller: AppController,
) -> tuple[QWidget, QObject]:
    from src.ui.views.panels.fence_diagram_panel import FenceDiagramPanel
    from src.ui.presenters.fence_diagram_presenter import FenceDiagramPresenter

    view = FenceDiagramPanel()
    presenter = FenceDiagramPresenter(view, store, controller)
    return view, presenter


# ── Centralized panel type registry ────────────────────────────────────────

PANEL_TYPE_CONFIG: dict[str, PanelConfig] = {
    "CoreImagePanel": PanelConfig(
        panel_type="CoreImagePanel",
        id_prefix="core_image",
        factory=_make_core_image_panel,
        ribbon_tab="Analysis",
    ),
    "DatasetPanel": PanelConfig(
        panel_type="DatasetPanel",
        id_prefix="dataset",
        factory=_make_dataset_panel,
        ribbon_tab="Home",
    ),
    "CoreStudioPanel": PanelConfig(
        panel_type="CoreStudioPanel",
        id_prefix="core_studio",
        factory=_make_core_studio_panel,
        ribbon_tab="Analysis",
    ),
    "FenceDiagramPanel": PanelConfig(
        panel_type="FenceDiagramPanel",
        id_prefix="fence_diagram",
        factory=_make_fence_diagram_panel,
        ribbon_tab="Analysis",
    ),
}
