"""Store — single source of truth for application state.

The Store is a QObject that owns the EntityContainer and is the
sole emitter of signals when state changes. Only the Store (and
eventually the AppController) should call CRUD operations on the container.

Presenters connect to Store signals to stay in sync.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.domain.store.container import EntityContainer


class Store(QObject):
    """Central state holder for the application.

    Wraps an EntityContainer and emits signals on every mutation.
    """

    # ── Signals ─────────────────────────────────────────────────
    # All signals emit (entity_id: str, entity_type: str)
    entityAdded = Signal(str, str)
    entityRemoved = Signal(str, str)
    entityUpdated = Signal(str, str)  # TODO: include field_name + old/new value?

    # TODO: batch signal — emitted after a batch of mutations completes
    # TODO: reset signal — emitted when the store is cleared / reloaded

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._container = EntityContainer()

    # ── Create ──────────────────────────────────────────────────

    def add(self, entity: object) -> str:
        """Add an entity. Returns its id. Emits entityAdded."""
        entity_id = self._container.add(entity)
        entity_type = type(entity).__name__
        self.entityAdded.emit(entity_id, entity_type)
        return entity_id

    # ── Read (delegated, no signals) ────────────────────────────

    def get(self, entity_id: str) -> object | None:
        """Return an entity by id, or None."""
        return self._container.get(entity_id)

    def get_many(self, entity_ids: list[str]) -> list[object]:
        """Return entities for the given ids (skips missing)."""
        return self._container.get_many(entity_ids)

    def get_field(self, entity_id: str, field_name: str) -> object | None:
        """Return a single field value from an entity."""
        return self._container.get_field(entity_id, field_name)

    def list_entities(
        self,
        entity_type: str | None = None,
        include_ids: bool = False,
    ) -> list[object] | list[tuple[str, object]]:
        """List entities, optionally filtered by type."""
        return self._container.list_entities(entity_type, include_ids)

    # ── Update ──────────────────────────────────────────────────

    def update_field(
        self, entity_id: str, field_name: str, value: object
    ) -> None:
        """Update a field on an entity. Emits entityUpdated."""
        self._container.update_field(entity_id, field_name, value)
        entity = self._container.get(entity_id)
        entity_type = type(entity).__name__
        self.entityUpdated.emit(entity_id, entity_type)

    # ── Delete ──────────────────────────────────────────────────

    def remove(self, entity_id: str) -> object:
        """Remove an entity. Emits entityRemoved. Returns the removed entity."""
        entity = self._container.remove(entity_id)
        entity_type = type(entity).__name__
        self.entityRemoved.emit(entity_id, entity_type)
        return entity

    # ── Stats (delegated, no signals) ───────────────────────────

    def count(self, entity_type: str | None = None) -> int:
        """Total entity count, or count of a specific type."""
        return self._container.count(entity_type)

    def summary(self) -> dict[str, int]:
        """Return a type → count breakdown."""
        return self._container.summary()

    # ── Lifecycle ───────────────────────────────────────────────

    def clear(self) -> None:
        """Remove all entities."""
        self._container.clear()
        # TODO: emit a reset/cleared signal

    # TODO: batch(...) — suppress intermediate signals, emit once at end
    # TODO: save / load — or delegate to a session module
