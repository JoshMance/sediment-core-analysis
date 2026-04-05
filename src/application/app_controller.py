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
from src.domain.entities.dataset_entity import DatasetEntity
from src.domain.entities.calibration_entity import CalibrationEntity
from src.domain.store import Store
from src.application.services.load_image import load_image
from src.application.services.load_csv import load_csv
from src.application.services.session_archive import save as archive_save
from src.application.services.session_archive import load as archive_load
from src.application.services.session_archive import ArchiveError
from src.application.workspace_state import WorkspaceState
from src.application.status_context import StatusContext
from src.application.recent_dirs import RecentDirs

logger = logging.getLogger(__name__)

# ── Column-type label helpers ─────────────────────────────────────────────────

def _dtype_to_label(dtype_str: str) -> str:
    """Map a pandas dtype string to a user-facing column type label."""
    if dtype_str.startswith("int") or dtype_str.startswith("float"):
        return "Number"
    if dtype_str.startswith("datetime"):
        return "Date"
    return "Text"


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
        self.status_context = StatusContext()
        self.recent_dirs = RecentDirs()

    def set_view_context(self, parts: list[str]) -> None:
        """Post context strings to the status bar right side.

        Called by presenters to report view-local state such as cursor
        coordinates or row/column position. Last call wins — no queuing.
        """
        self.status_context.set(parts)

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

    def create_cropped_image(
        self,
        name: str,
        data: object,
        parent_id: str,
    ) -> str | None:
        """Create a cropped ImageEntity as a child of a parent image.

        The child inherits the parent's calibration_id. The parent's
        child_ids list is updated to include the new entity.

        Args:
            name: Display name for the cropped image.
            data: Cropped image array (H, W, 3) uint8.
            parent_id: ID of the parent ImageEntity.

        Returns:
            The entity id assigned by the Store, or None if the parent
            was not found.
        """
        parent = self._store.get(parent_id)
        if not isinstance(parent, ImageEntity):
            logger.error("create_cropped_image: parent '%s' not found or not an ImageEntity", parent_id)
            return None

        entity = ImageEntity(
            name=name,
            data=data,
            parent_id=parent_id,
            calibration_id=parent.calibration_id,
        )
        child_id = self._store.add(entity)

        # Update parent's child_ids
        updated_children = list(parent.child_ids) + [child_id]
        self._store.update_field(parent_id, "child_ids", updated_children)

        return child_id

    def delete_entity(self, entity_id: str) -> object:
        """Remove an entity from the Store.

        Args:
            entity_id: The id of the entity to remove.

        Returns:
            The removed entity.
        """
        return self._store.remove(entity_id)

    def rename_entity(self, entity_id: str, new_name: str) -> None:
        """Rename an entity in the Store.

        Args:
            entity_id: The id of the entity to rename.
            new_name: The new display name.
        """
        self._store.update_field(entity_id, "name", new_name)

    def create_dataset_entity(self, file_path: str) -> str | None:
        """Load a CSV from disk and add it to the Store as a DatasetEntity.

        Args:
            file_path: Absolute path to a CSV file.

        Returns:
            The entity id assigned by the Store, or None if loading failed.
        """
        path = Path(file_path)
        try:
            df = load_csv(path)
        except (FileNotFoundError, ValueError) as e:
            logger.error("Failed to load CSV: %s", e)
            return None

        entity = DatasetEntity(
            name=path.name,
            file_path=path,
            data=df,
            columns=list(df.columns),
            column_types={col: _dtype_to_label(str(df[col].dtype)) for col in df.columns},
        )
        return self._store.add(entity)

    def rename_dataset_column(self, entity_id: str, old_name: str, new_name: str) -> None:
        """Rename a column on a DatasetEntity in the Store.

        Args:
            entity_id: ID of the DatasetEntity.
            old_name: Current column name.
            new_name: New column name.
        """
        entity = self._store.get(entity_id)
        if entity is None or entity.data is None:
            return
        entity.data = entity.data.rename(columns={old_name: new_name})
        entity.columns = list(entity.data.columns)
        entity.column_types = {
            (new_name if col == old_name else col): label
            for col, label in entity.column_types.items()
        }
        self._store.update_field(entity_id, "data", entity.data)

    def change_dataset_column_type(
        self, entity_id: str, col_name: str, new_type: str
    ) -> None:
        """Update the display type label for a column. Does not mutate the DataFrame.

        Args:
            entity_id: ID of the DatasetEntity.
            col_name: Column to re-label.
            new_type: One of 'Text', 'Number', 'Date'.
        """
        entity = self._store.get(entity_id)
        if entity is None:
            return
        entity.column_types[col_name] = new_type
        self._store.update_field(entity_id, "column_types", entity.column_types)

    def update_dataset_cell(
        self, entity_id: str, row: int, col: int, value: object
    ) -> None:
        """Update a single cell value on a DatasetEntity in the Store.

        Args:
            entity_id: ID of the DatasetEntity.
            row: Row index.
            col: Column index.
            value: New cell value.
        """
        entity = self._store.get(entity_id)
        if entity is None or entity.data is None:
            return
        try:
            entity.data.iloc[row, col] = value
        except Exception as e:
            logger.warning("Cell update failed at (%d, %d): %s", row, col, e)
            return
        self._store.update_field(entity_id, "data", entity.data)

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

        # Add entities to Store and load asset data
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
            elif isinstance(entity, DatasetEntity) and entity.asset_ref:
                try:
                    import pandas as pd
                    entity.data = pd.read_csv(entity.asset_ref)
                    entity.columns = list(entity.data.columns)
                    entity.column_types = {
                        col: _dtype_to_label(str(entity.data[col].dtype))
                        for col in entity.data.columns
                    }
                except Exception as e:
                    logger.warning("Could not load CSV data for %s: %s", entity.id, e)
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