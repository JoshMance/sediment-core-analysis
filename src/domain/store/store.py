"""Store — single source of truth for application state.

The Store is a QObject that owns the EntityContainer and is the
sole emitter of signals when state changes. Only the Store (and
eventually the AppController) should call CRUD operations on the container.

Presenters connect to Store signals to stay in sync.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from src.domain.store.container import EntityContainer
from src.domain.entities.propagation import PROPAGATION_RULES


class Store(QObject):
    """Central state holder for the application.

    Wraps an EntityContainer and emits signals on every mutation.
    """

    # ── Signals ─────────────────────────────────────────────────
    # All signals emit (entity_id: str, entity_type: str)
    entityAdded = Signal(str, str)
    entityRemoved = Signal(str, str)
    entityUpdated = Signal(str, str)  # TODO: include field_name + old/new value?
    storeReset = Signal()             # emitted after all entities are cleared

    # TODO: batch signal — emitted after a batch of mutations completes

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
        """Update a field on an entity and cascade to related entities.

        Emits ``entityUpdated`` for every entity that is written.
        Propagation targets are determined by ``PROPAGATION_RULES`` in
        ``src/domain/entities/propagation.py``.  Traversal is BFS with a
        visited-set so cycles in the entity graph cannot cause infinite loops.
        """
        queue: list[str] = [entity_id]
        visited: set[str] = set()

        while queue:
            eid = queue.pop(0)
            if eid in visited:
                continue
            visited.add(eid)

            self._container.update_field(eid, field_name, value)
            entity = self._container.get(eid)
            entity_type = type(entity).__name__
            self.entityUpdated.emit(eid, entity_type)

            for rule in PROPAGATION_RULES:
                if rule.entity_type == entity_type and rule.field == field_name:
                    related = getattr(entity, rule.via, None)
                    if isinstance(related, list):
                        queue.extend(related)
                    elif isinstance(related, str) and related:
                        queue.append(related)

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
        """Remove all entities. Emits storeReset."""
        self._container.clear()
        self.storeReset.emit()

    # TODO: batch(...) — suppress intermediate signals, emit once at end
    # TODO: save / load — or delegate to a session module
