"""AppController — core process that orchestrates the app.

Receives intents from Presenters, performs I/O via services,
constructs entities, and delegates storage to the Store.
The AppController is the only component that writes to the Store.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from src.domain.entities.image_entity import ImageEntity
from src.domain.store import Store
from src.application.services.load_image import load_image

logger = logging.getLogger(__name__)


class AppController:
    """Orchestrates mutations: intent -> I/O -> entity -> Store."""

    def __init__(
        self,
        store: Store,
        component_watcher: Callable[[str, object], None] | None = None,
    ) -> None:
        self._store = store
        self._component_watcher = component_watcher

    def _watch(self, name: str, obj: object) -> None:
        """Register a runtime-created component with the dev logger (if any)."""
        if self._component_watcher:
            self._component_watcher(name, obj)

    def create_image_entity(self, file_path: str) -> str | None:
        """Load an image from disk and add it to the Store.

        Args:
            file_path: Absolute path to an image file.

        Returns:
            The entity id assigned by the Store, or None if loading failed.
        """
        path = Path(file_path)

        try:
            data = load_image(path)
        except (FileNotFoundError, ValueError) as e:
            logger.error("Failed to load image: %s", e)
            return None

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