"""WorkspaceState — tracks which panels are currently open in the workspace."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, Signal

from src.domain.store import Store


@dataclass
class WorkspaceEntry:
    """Describes a single open panel in the workspace."""
    panel_id: str
    panel_type: str
    target_entity_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "panel_id": self.panel_id,
            "panel_type": self.panel_type,
            "target_entity_id": self.target_entity_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceEntry":
        panel_id = data["panel_id"]
        target_entity_id = data.get("target_entity_id")
        return cls(
            panel_id=panel_id,
            panel_type=data["panel_type"],
            target_entity_id=target_entity_id,
        )


class WorkspaceState(QObject):
    """Application-layer record of the logical workspace contents.

    Emits signals when panels are opened, closed, or need focus.
    The UI layer reacts to these signals — the application layer never
    touches widgets directly.
    """

    panelAdded = Signal(object)        # WorkspaceEntry
    panelRemoved = Signal(str)         # panel_id
    panelFocusRequested = Signal(str)  # panel_id

    def __init__(self, store: Store | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: dict[str, WorkspaceEntry] = {}
        self._active_panel_id: str | None = None
        if store is not None:
            store.entityRemoved.connect(self._on_entity_removed)
            store.storeReset.connect(self.clear)

    def open(self, entry: WorkspaceEntry) -> None:
        """Open a panel, or request focus if already open."""
        if entry.panel_id in self._entries:
            self.panelFocusRequested.emit(entry.panel_id)
        else:
            self._entries[entry.panel_id] = entry
            self.panelAdded.emit(entry)

    def close(self, panel_id: str) -> None:
        """Record that a panel has been closed."""
        self._entries.pop(panel_id, None)
        if self._active_panel_id == panel_id:
            self._active_panel_id = None
        self.panelRemoved.emit(panel_id)

    def is_open(self, panel_id: str) -> bool:
        """Return True if a panel is currently open for this panel id."""
        return panel_id in self._entries

    def clear(self) -> None:
        """Close all panels. Emits panelRemoved for each open entry."""
        self._active_panel_id = None
        for panel_id in list(self._entries):
            self.close(panel_id)

    def set_active_panel(self, panel_id: str | None) -> None:
        """Called by the UI when the focused tab changes."""
        self._active_panel_id = panel_id if panel_id in self._entries else None

    @property
    def active_entity_id(self) -> str | None:
        """target_entity_id of the currently focused panel, or None."""
        if self._active_panel_id is None:
            return None
        entry = self._entries.get(self._active_panel_id)
        return entry.target_entity_id if entry else None

    # ── Store signal handlers ─────────────────────────────────

    def _on_entity_removed(self, entity_id: str, _entity_type: str) -> None:
        to_close = [
            panel_id
            for panel_id, entry in self._entries.items()
            if entry.target_entity_id == entity_id
        ]
        for panel_id in to_close:
            self.close(panel_id)
