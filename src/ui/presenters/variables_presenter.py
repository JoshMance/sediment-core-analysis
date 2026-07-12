"""
VariablesPresenter - connects VariablesList view to Store and AppController

Follows MVP pattern where Presenter:
- Handles View events → calls AppController methods
- Handles Store signals → updates the View's display
- Can read Store directly via its public API when needed
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from src.ui.views.shell.variables_list import VariablesList
from src.ui.views.shell.preview import PreviewPanel
from src.domain.store import Store
from src.domain.entities.dataset_entity import DatasetEntity
from src.domain.entities.core_entity import CoreEntity
from src.application import AppController


class VariablesPresenter(QObject):
    def __init__(
        self,
        view: VariablesList,
        preview: PreviewPanel,
        store: Store,
        controller: AppController,
    ):
        super().__init__()
        self.view = view
        self._preview = preview
        self.store = store
        self.controller = controller

        # ── Listen to Store signals ─────────────────────────
        self.store.entityAdded.connect(self._on_entity_added)
        self.store.entityRemoved.connect(self._on_entity_removed)
        self.store.storeReset.connect(self._on_store_reset)

        # ── Listen to View signals ──────────────────────────
        self.view.deleteRequested.connect(self._on_delete_requested)
        self.view.renameRequested.connect(self._on_rename_requested)
        self.view.entityOpenRequested.connect(self._on_entity_open_requested)
        self.view.openInCoreStudioRequested.connect(self._on_open_in_core_studio_requested)
        self.view.entitySelected.connect(self._on_entity_selected)

        # ── Listen to Store signals ─────────────────────────
        self.store.entityUpdated.connect(self._on_entity_updated)

    # ── Store → View ────────────────────────────────────────

    def _on_entity_added(self, entity_id: str, entity_type: str):
        """Store says an entity was added - read it and tell the view."""
        entity = self.store.get(entity_id)
        name = _display_name(entity, fallback=str(entity_id))
        display_type = entity_type.removesuffix("Entity")

        # Determine parent for tree nesting.
        parent_id = (
            getattr(entity, "parent_core_id", None)
            or getattr(entity, "parent_id", None)
        )

        # File path for OS-native icon.
        file_path = (
            getattr(entity, "file_path", None)
            or getattr(entity, "source_file_path", None)
        )
        file_path_str = str(file_path) if file_path else None

        self.view.add_row(
            entity_id, name, display_type,
            parent_id=parent_id, file_path=file_path_str,
        )

    def _on_entity_removed(self, entity_id: str, entity_type: str):
        """Store says an entity was removed — tell the view."""
        self.view.remove_row(entity_id)
        self._preview.clear()

    def _on_store_reset(self) -> None:
        """Store was cleared (new/load session) — wipe the tree."""
        self.view.clear_rows()
        self._preview.clear()

    # ── View → PreviewPanel ───────────────────────────────

    def _on_entity_selected(self, entity_id: str) -> None:
        """User clicked a row — push metadata to the preview panel."""
        entity = self.store.get(entity_id)
        if entity is None:
            self._preview.clear()
            return
        self._preview.show_entity(_build_preview_rows(entity))

    # ── View → AppController ──────────────────────────────

    def _on_entity_updated(self, entity_id: str, _entity_type: str):
        """Store says an entity was updated — refresh the row name."""
        entity = self.store.get(entity_id)
        if entity is not None:
            self.view.update_row_name(entity_id, _display_name(entity, fallback=str(entity_id)))

    def _on_delete_requested(self, entity_id: str):
        """User clicked Delete — warn if a dataset is referenced, then route to AppController."""
        entity = self.store.get(entity_id)
        if isinstance(entity, DatasetEntity):
            referencing: list[str] = []
            for core in self.store.list_entities("CoreEntity"):
                if not isinstance(core, CoreEntity):
                    continue
                if any(p.get("dataset_id") == entity_id for p in core.dataset_plots):
                    referencing.append(core.name)
            if referencing:
                names = ", ".join(referencing)
                answer = QMessageBox.question(
                    self.view,
                    "Delete dataset",
                    f"'{entity.name}' is used as a data plot in: {names}.\n\n"
                    "Deleting it will remove those plots. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
        self.controller.delete_entity(entity_id)

    def _on_rename_requested(self, entity_id: str, new_name: str):
        """User confirmed a rename — route to AppController."""
        self.controller.rename_entity(entity_id, new_name)

    def _on_entity_open_requested(self, entity_id: str):
        """User double-clicked a row — open the entity in the workspace."""
        self.controller.open_in_workspace(entity_id)

    def _on_open_in_core_studio_requested(self, core_id: str) -> None:
        """User requested opening an entity in Core Studio via context menu."""
        self.controller.open_core_in_studio(core_id)


# ── Preview metadata builders ─────────────────────────────────────────────────

def _build_preview_rows(entity) -> list[tuple[str, str]]:
    """Return (label, value) pairs for any entity type."""
    entity_type = type(entity).__name__.removesuffix("Entity")
    rows: list[tuple[str, str]] = [
        ("Name", getattr(entity, "name", "—")),
        ("Type", entity_type),
    ]
    # Type-specific rows
    data = getattr(entity, "data", None)
    if entity_type == "Dataset" and data is not None:
        rows.append(("Rows", str(len(data))))
        rows.append(("Columns", str(len(data.columns))))
    elif entity_type == "Core" and data is not None:
        h, w = data.shape[:2]
        rows.append(("Width", str(w)))
        rows.append(("Height", str(h)))
        rows.append(("Draft", "Yes" if bool(getattr(entity, "is_draft", False)) else "No"))
    elif entity_type == "Core":
        rows.append(("Draft", "Yes" if bool(getattr(entity, "is_draft", False)) else "No"))
    file_path = (
        getattr(entity, "file_path", None)
        or getattr(entity, "source_file_path", None)
    )
    if file_path:
        from pathlib import Path
        rows.append(("File", Path(file_path).name))
    return rows


def _display_name(entity: object, fallback: str) -> str:
    """Return the VariablesList label for an entity."""
    base = getattr(entity, "name", fallback)
    if bool(getattr(entity, "is_draft", False)):
        return f"{base} (draft)"
    return base
