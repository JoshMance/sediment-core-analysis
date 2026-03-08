"""WorkspaceState — tracks which panels are currently open in the workspace."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


@dataclass
class WorkspaceEntry:
    """Describes a single open panel in the workspace."""
    entity_id: str
    panel_type: str

    def to_dict(self) -> dict:
        return {"entity_id": self.entity_id, "panel_type": self.panel_type}

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceEntry":
        return cls(entity_id=data["entity_id"], panel_type=data["panel_type"])


class WorkspaceState(QObject):
    """Application-layer record of the logical workspace contents.

    Emits signals when panels are opened, closed, or need focus.
    The UI layer reacts to these signals — the application layer never
    touches widgets directly.
    """

    panelAdded = Signal(object)        # WorkspaceEntry
    panelRemoved = Signal(str)         # entity_id
    panelFocusRequested = Signal(str)  # entity_id

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._entries: dict[str, WorkspaceEntry] = {}

    def open(self, entry: WorkspaceEntry) -> None:
        """Open a panel, or request focus if already open."""
        if entry.entity_id in self._entries:
            self.panelFocusRequested.emit(entry.entity_id)
        else:
            self._entries[entry.entity_id] = entry
            self.panelAdded.emit(entry)

    def close(self, entity_id: str) -> None:
        """Record that a panel has been closed."""
        self._entries.pop(entity_id, None)
        self.panelRemoved.emit(entity_id)

    def is_open(self, entity_id: str) -> bool:
        """Return True if a panel is currently open for this entity."""
        return entity_id in self._entries

    def clear(self) -> None:
        """Close all panels. Emits panelRemoved for each open entry."""
        for entity_id in list(self._entries):
            self.close(entity_id)
