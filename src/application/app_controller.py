"""AppController — core process that orchestrates the app.

Receives intents from Presenters, performs I/O via services,
constructs entities, and delegates storage to the Store.
The AppController is the only component that writes to the Store.
"""
from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

import imageio.v3 as iio

from src.domain.entities.image_entity import ImageEntity
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store
from src.application.services.load_image import load_image
from src.application.services.session_archive import save as archive_save
from src.application.services.session_archive import load as archive_load
from src.application.services.session_archive import ArchiveError
from src.application.workspace_state import WorkspaceState

logger = logging.getLogger(__name__)


class AppController:
    """Orchestrates mutations: intent -> I/O -> entity -> Store."""

    def __init__(
        self,
        store: Store,
        workspace_state: WorkspaceState | None = None,
        component_watcher: Callable[[str, object], None] | None = None,
    ) -> None:
        self._store = store
        self._workspace_state = workspace_state
        self._component_watcher = component_watcher
        self._session_temp_dir: tempfile.TemporaryDirectory | None = None

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

    def create_core_entity(
        self,
        name: str,
        data: object,
        source_image_id: str | None = None,
    ) -> str:
        """Construct a CoreEntity and add it to the Store.

        Args:
            name: Display name for the core.
            data: Cropped image array (H, W, 3) uint8.
            source_image_id: ID of the source ImageEntity, if any.

        Returns:
            The entity id assigned by the Store.
        """
        entity = CoreEntity(name=name, data=data, source_image_id=source_image_id)
        return self._store.add(entity)

    def delete_entity(self, entity_id: str) -> object:
        """Remove an entity from the Store.

        Args:
            entity_id: The id of the entity to remove.

        Returns:
            The removed entity.
        """
        return self._store.remove(entity_id)

    def open_in_workspace(self, entity_id: str) -> None:
        """Open an entity as a panel in the workspace.

        Delegates to WorkspaceService which validates the entity and
        determines the correct panel type. Silently ignored if no
        WorkspaceState is configured.

        Args:
            entity_id: The id of the entity to open.
        """
        if self._workspace_state is None:
            return
        from src.application.services import workspace_service
        try:
            workspace_service.open_entity(entity_id, self._store, self._workspace_state)
        except ValueError as e:
            logger.warning("open_in_workspace: %s", e)

    # ── Session persistence ──────────────────────────────────────────────────

    def new_session(self) -> None:
        """Clear all entities and close all panels, resetting to a blank session."""
        self._cleanup_temp_dir()
        self._store.clear()
        if self._workspace_state is not None:
            self._workspace_state.clear()
        logger.info("New session started.")

    def save_session(self, path: Path) -> None:
        """Save the current session to a .sedivis archive.

        Args:
            path: Destination file path.

        Raises:
            ArchiveError: If any required asset cannot be bundled.
        """
        entities = self._store.list_entities()
        workspace_entries = (
            list(self._workspace_state._entries.values())
            if self._workspace_state is not None
            else []
        )
        archive_save(path, entities, workspace_entries)
        logger.info("Session saved to %s", path)

    def load_session(self, path: Path) -> None:
        """Load a .sedivis archive, replacing the current session.

        Clears the Store and WorkspaceState first, then reconstructs
        all entities and reopens workspace panels.

        Args:
            path: Path to the .sedivis archive.

        Raises:
            ArchiveError: If the archive is invalid, corrupt, or has missing assets.
        """
        # Reset current state
        self._cleanup_temp_dir()
        self._store.clear()
        if self._workspace_state is not None:
            self._workspace_state.clear()

        # Extract archive to a fresh temp dir (owned for the session lifetime)
        self._session_temp_dir = tempfile.TemporaryDirectory(prefix="sedivis_")
        extract_dir = Path(self._session_temp_dir.name)

        entities, workspace_entries = archive_load(path, extract_dir)

        # Add entities to Store and load pixel data
        for entity in entities:
            if isinstance(entity, ImageEntity) and entity.file_path:
                try:
                    entity.data = load_image(entity.file_path)
                except Exception as e:
                    logger.warning("Could not load pixels for %s: %s", entity.id, e)
            elif isinstance(entity, CoreEntity) and entity.asset_ref:
                try:
                    entity.data = iio.imread(entity.asset_ref)
                except Exception as e:
                    logger.warning("Could not load core pixels for %s: %s", entity.id, e)
            self._store.add(entity)

        # Reopen workspace panels
        if self._workspace_state is not None:
            for entry in workspace_entries:
                self._workspace_state.open(entry)

        logger.info("Session loaded from %s (%d entities)", path, len(entities))

    def _cleanup_temp_dir(self) -> None:
        """Clean up the previous session's temp directory, if any."""
        if self._session_temp_dir is not None:
            try:
                self._session_temp_dir.cleanup()
            except Exception as e:
                logger.warning("Failed to clean up session temp dir: %s", e)
            self._session_temp_dir = None