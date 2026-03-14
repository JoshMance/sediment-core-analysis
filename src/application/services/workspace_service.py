"""WorkspaceService — maps entity types to panel types and opens them."""
from __future__ import annotations

from src.domain.store import Store
from src.application.workspace_state import WorkspaceEntry, WorkspaceState

_PANEL_TYPE_MAP: dict[str, str] = {
    "ImageEntity": "ImagePanel",
    "CsvEntity": "CsvPanel",
}


def open_entity(entity_id: str, store: Store, workspace_state: WorkspaceState) -> None:
    """Validate an entity exists and open it in the workspace.

    Silently does nothing if the entity type has no registered panel type —
    this is expected for entity types (e.g. CoreEntity) that don't yet have
    a panel implementation.

    Args:
        entity_id: ID of the entity to open.
        store: The domain Store to validate existence.
        workspace_state: The application workspace state to update.

    Raises:
        ValueError: If the entity does not exist.
    """
    entity = store.get(entity_id)
    if entity is None:
        raise ValueError(f"No entity with id '{entity_id}'.")

    entity_type = type(entity).__name__
    panel_type = _PANEL_TYPE_MAP.get(entity_type)
    if panel_type is None:
        return  # No panel registered for this type yet — not an error

    workspace_state.open(WorkspaceEntry(entity_id=entity_id, panel_type=panel_type))
