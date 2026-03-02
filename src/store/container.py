"""Entity container — passive in-memory bucket for entity instances.

Provides type-agnostic CRUD operations and basic stats.
This module is a data holder only. It does not emit signals,
enforce domain rules, manage persistence, or interpret entity meaning.

Only store.py should perform CRUD operations on this container.
Tests may read attributes directly or use the API when testing container in isolation.
"""
from __future__ import annotations

import uuid
from dataclasses import fields

from src.entities.registry import ENTITY_TYPES


class EntityContainer:
    """Stores entity instances keyed by unique ID.

    Entities are any dataclass instance whose class is registered
    in the entity registry. Each entity must have an ``id`` field
    (str | None). If ``id`` is None on add, one is assigned automatically.
    """

    def __init__(self) -> None:
        self._entities: dict[str, object] = {}
        self._type_index: dict[str, set[str]] = {}  # type_name -> set of ids

    # ── Create ──────────────────────────────────────────────────

    def add(self, entity: object) -> str:
        """Add an entity to the container.

        If the entity's ``id`` is None, a UUID is assigned.
        Returns the entity's id.

        Raises:
            TypeError: If the entity is not a registered entity type.
            ValueError: If an entity with the same id already exists.
        """
        type_name = type(entity).__name__
        if type_name not in ENTITY_TYPES:
            raise TypeError(
                f"Unknown entity type '{type_name}'. "
                f"Registered types: {list(ENTITY_TYPES.keys())}"
            )

        if entity.id is None:
            entity.id = uuid.uuid4().hex

        if entity.id in self._entities:
            raise ValueError(f"Entity with id '{entity.id}' already exists.")

        self._entities[entity.id] = entity

        if type_name not in self._type_index:
            self._type_index[type_name] = set()
        self._type_index[type_name].add(entity.id)

        return entity.id

    # ── Read ────────────────────────────────────────────────────

    def get(self, entity_id: str) -> object | None:
        """Return an entity by id, or None if not found."""
        return self._entities.get(entity_id)

    def get_many(self, entity_ids: list[str]) -> list[object]:
        """Return a list of entities for the given ids (skips missing)."""
        return [
            self._entities[eid]
            for eid in entity_ids
            if eid in self._entities
        ]

    def get_field(self, entity_id: str, field_name: str) -> object | None:
        """Return a single field value from an entity.

        Returns None if the entity or field doesn't exist.
        """
        entity = self._entities.get(entity_id)
        if entity is None:
            return None
        return getattr(entity, field_name, None)

    def list_entities(
        self,
        entity_type: str | None = None,
        include_ids: bool = False,
    ) -> list[object] | list[tuple[str, object]]:
        """List entities, optionally filtered by type.

        Args:
            entity_type: If provided, only return entities of this type.
            include_ids: If True, return list of (id, entity) tuples.

        Returns:
            List of entities, or list of (id, entity) tuples.
        """
        if entity_type is not None:
            ids = self._type_index.get(entity_type, set())
            entities = [(eid, self._entities[eid]) for eid in ids]
        else:
            entities = list(self._entities.items())

        if include_ids:
            return entities
        return [entity for _, entity in entities]

    # ── Update ──────────────────────────────────────────────────

    def update_field(
        self, entity_id: str, field_name: str, value: object
    ) -> None:
        """Update a single field on an entity.

        Raises:
            KeyError: If the entity doesn't exist.
            AttributeError: If the field doesn't exist on the entity.
        """
        entity = self._entities.get(entity_id)
        if entity is None:
            raise KeyError(f"No entity with id '{entity_id}'.")

        # Validate the field exists on the dataclass
        field_names = {f.name for f in fields(entity)}
        if field_name not in field_names:
            raise AttributeError(
                f"'{type(entity).__name__}' has no field '{field_name}'."
            )

        setattr(entity, field_name, value)

    # ── Delete ──────────────────────────────────────────────────

    def remove(self, entity_id: str) -> object:
        """Remove an entity by id and return it.

        Raises:
            KeyError: If the entity doesn't exist.
        """
        entity = self._entities.pop(entity_id, None)
        if entity is None:
            raise KeyError(f"No entity with id '{entity_id}'.")

        type_name = type(entity).__name__
        if type_name in self._type_index:
            self._type_index[type_name].discard(entity_id)
            if not self._type_index[type_name]:
                del self._type_index[type_name]

        return entity

    # ── Stats / Query ───────────────────────────────────────────

    def count(self, entity_type: str | None = None) -> int:
        """Total entity count, or count of a specific type."""
        if entity_type is not None:
            return len(self._type_index.get(entity_type, set()))
        return len(self._entities)

    def summary(self) -> dict[str, int]:
        """Return a type → count breakdown of all stored entities."""
        return {
            type_name: len(ids)
            for type_name, ids in self._type_index.items()
        }

    # ── Internals ───────────────────────────────────────────────

    def clear(self) -> None:
        """Remove all entities."""
        self._entities.clear()
        self._type_index.clear()
