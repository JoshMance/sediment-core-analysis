"""Controller — write coordinator for the application.

Receives intents from Presenters, performs I/O via loaders,
constructs entities, and delegates storage to the Store.
The Controller is the only component that writes to the Store.
"""
from __future__ import annotations

from pathlib import Path

from src.entities.image_entity import ImageEntity
from src.store import Store
from src.controller.loaders import load_image


class Controller:
    """Orchestrates mutations: intent → I/O → entity → Store."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def create_image_entity(self, file_path: str) -> str:
        """Load an image from disk and add it to the Store.

        Args:
            file_path: Absolute path to an image file.

        Returns:
            The entity id assigned by the Store.
        """
        path = Path(file_path)
        data = load_image(path)

        entity = ImageEntity(
            name=path.name,
            file_path=path,
            data=data,
        )

        return self._store.add(entity)
    def delete_entity(self, entity_id: str) -> object:
        """Remove an entity from the Store.

        Args:
            entity_id: The id of the entity to remove.

        Returns:
            The removed entity.
        """
        return self._store.remove(entity_id)