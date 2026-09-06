"""AppController — core process that orchestrates the app.

Receives intents from Presenters, performs I/O via services,
constructs entities, and delegates storage to the Store.
The AppController is the only component that writes to the Store.
"""
from __future__ import annotations

import copy
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

import imageio.v3 as iio

from src.domain.entities.core_entity import CoreEntity
from src.domain.entities.dataset_entity import DatasetEntity
from src.domain.store import Store
from src.application.services.load_image import load_image
from src.application.services.load_csv import load_csv
from src.application.services.resolve_image import resolve as resolve_image
from src.application.services.session_archive import save as archive_save
from src.application.services.session_archive import load as archive_load
from src.application.services.session_archive import ArchiveError
from src.application.workspace_state import WorkspaceState, WorkspaceEntry
from src.application.status_context import StatusContext
from src.application.ribbon_context import RibbonContext
from src.application.recent_dirs import RecentDirs

logger = logging.getLogger(__name__)

_CORE_STUDIO_TAB_PREFIX = "core_studio::"
_BLANK_CORE_STUDIO_PANEL_ID = "core_studio::blank"

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
        self._resolved_cache: dict[str, object] = {}  # entity_id -> ndarray
        self.status_context = StatusContext()
        self.ribbon_context = RibbonContext()
        self.recent_dirs = RecentDirs()

        # Invalidate resolved-image cache on store mutations.
        store.entityUpdated.connect(self._on_store_entity_updated)
        store.entityRemoved.connect(self._on_store_entity_removed)
        store.storeReset.connect(self._resolved_cache.clear)

    def _on_store_entity_updated(self, entity_id: str, entity_type: str) -> None:
        self._resolved_cache.pop(entity_id, None)

    def _on_store_entity_removed(self, entity_id: str, entity_type: str) -> None:
        self._resolved_cache.pop(entity_id, None)

    def get_resolved_data(self, entity_id: str) -> object:
        """Return the display image for a core: base_data with filter_stack applied.

        Results are cached until the entity is updated or removed.  Returns
        ``None`` if the entity does not exist or has no pixel data.
        """
        import numpy as np
        if entity_id in self._resolved_cache:
            return self._resolved_cache[entity_id]
        entity = self._store.get(entity_id)
        if not isinstance(entity, CoreEntity) or entity.base_data is None:
            return None
        resolved = resolve_image(entity.base_data, entity.filter_stack)
        self._resolved_cache[entity_id] = resolved
        return resolved

    def set_filter_stack(self, entity_id: str, stack: list[dict]) -> None:
        """Replace the filter stack for a core.

        Propagation to child cores is handled automatically by the Store via
        PROPAGATION_RULES in src/domain/entities/propagation.py.
        Cache invalidation happens via the entityUpdated signal.
        """
        self._store.update_field(entity_id, "filter_stack", stack)

    def set_view_context(self, parts: list[str]) -> None:
        """Post context strings to the status bar right side.

        Called by presenters to report view-local state such as cursor
        coordinates or row/column position. Last call wins — no queuing.
        """
        self.status_context.set(parts)

    def set_ribbon_tab(self, tab_name: str) -> None:
        """Request that the ribbon switch to the given tab.

        Called by presenters to synchronise the ribbon with the current
        context (e.g. a panel gaining focus). Last call wins.
        """
        self.ribbon_context.set_tab(tab_name)

    def _watch(self, name: str, obj: object) -> None:
        """Register a runtime-created component with the dev logger (if any)."""
        if self._component_watcher:
            self._component_watcher(name, obj)

    def import_core_from_image(self, file_path: str) -> str | None:
        """Load an image from disk and add it to the Store as a CoreEntity.

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

        return self.create_core_entity(
            name=path.name,
            base_data=data,
            source_file_path=path,
            derivation_type="import",
            derivation_params={},
            is_draft=False,
        )

    def create_core_entity(
        self,
        name: str,
        base_data: object,
        source_file_path: str | Path | None = None,
        parent_core_id: str | None = None,
        derivation_type: str = "import",
        derivation_params: dict | None = None,
        mm_per_px: float = 0.0,
        filter_stack: list[dict] | None = None,
        is_draft: bool = False,
    ) -> str:
        """Construct a CoreEntity and add it to the Store.

        Args:
            name: Display name for the core.
            base_data: Raw image array (H, W, 3) uint8 — write-once source pixels.
            source_file_path: Original import source path, if any.
            parent_core_id: Parent core id if derived from another core.
            derivation_type: Derivation operation type.
            derivation_params: Derivation metadata payload.
            mm_per_px: Millimetres per pixel. 0.0 means uncalibrated.
            filter_stack: Initial filter stack. Defaults to empty.
            is_draft: True if this core is still being prepared.

        Returns:
            The entity id assigned by the Store.
        """
        entity = CoreEntity(
            name=name,
            base_data=base_data,
            source_file_path=Path(source_file_path) if source_file_path is not None else None,
            parent_core_id=parent_core_id,
            derivation_type=derivation_type,
            derivation_params=derivation_params or {},
            mm_per_px=mm_per_px,
            filter_stack=filter_stack if filter_stack is not None else [],
            is_draft=is_draft,
        )
        return self._store.add(entity)

    def create_child_core(
        self,
        parent_core_id: str,
        base_data: object,
        name: str | None = None,
        derivation_type: str = "crop",
        derivation_params: dict | None = None,
        is_draft: bool = True,
    ) -> str | None:
        """Create a derived child CoreEntity from an existing parent core.

        The child starts with a copy of the parent's current filter_stack.
        If the parent's filter_stack is later changed, the Store propagation
        rules cascade the new stack to the child automatically.

        Args:
            parent_core_id: ID of the source parent core.
            base_data: Child core raw pixel data (write-once).
            name: Optional explicit child name.
            derivation_type: Derivation operation type.
            derivation_params: Derivation metadata payload.
            is_draft: True while the child core is still being prepared.

        Returns:
            The created child core id, or None if parent is missing/invalid.
        """
        parent = self._store.get(parent_core_id)
        if not isinstance(parent, CoreEntity):
            logger.warning("create_child_core: invalid parent '%s'", parent_core_id)
            return None

        if name is None:
            stem = parent.name.rsplit(".", 1)[0] if "." in parent.name else parent.name
            name = f"{stem}_{derivation_type}"

        child_id = self._create_derived_core(
            parent_core_id,
            parent,
            base_data,
            name,
            derivation_type,
            derivation_params or {},
            is_draft,
        )
        updated_children = list(parent.child_core_ids) + [child_id]
        self._store.update_field(parent_core_id, "child_core_ids", updated_children)
        return child_id

    def _create_derived_core(
        self,
        parent_core_id: str,
        parent: CoreEntity,
        base_data: object,
        name: str,
        derivation_type: str,
        derivation_params: dict,
        is_draft: bool,
    ) -> str:
        """Create one child core with an independent metadata snapshot."""
        child = CoreEntity(
            name=name,
            base_data=base_data,
            source_file_path=parent.source_file_path,
            parent_core_id=parent_core_id,
            derivation_type=derivation_type,
            derivation_params=derivation_params,
            mm_per_px=parent.mm_per_px,
            illuminant=parent.illuminant,
            filter_stack=copy.deepcopy(parent.filter_stack),
            is_draft=is_draft,
        )
        return self._store.add(child)

    def split_core(
        self,
        source_core_id: str,
        axis: str,
        split_position: int,
        first_name: str,
        second_name: str,
    ) -> tuple[str, str] | None:
        """Split a core image along the requested axis into two child cores.

        The source core remains unchanged. Both children inherit the source's
        calibration, illuminant, and filter stack, and record the raw-pixel
        bounds that produced them.
        """
        import numpy as np

        source = self._store.get(source_core_id)
        if not isinstance(source, CoreEntity) or source.base_data is None:
            logger.warning("split_core: invalid source '%s'", source_core_id)
            return None

        if axis not in {"horizontal", "vertical"}:
            logger.warning("split_core: unsupported axis '%s'", axis)
            return None
        length = source.base_data.shape[0] if axis == "horizontal" else source.base_data.shape[1]
        if not 0 < split_position < length:
            logger.warning("split_core: position %s outside %s axis length %s", split_position, axis, length)
            return None

        if axis == "horizontal":
            first_data = np.ascontiguousarray(source.base_data[:split_position].copy())
            second_data = np.ascontiguousarray(source.base_data[split_position:].copy())
            first_bounds = {"axis": axis, "start_y": 0, "end_y": split_position}
            second_bounds = {"axis": axis, "start_y": split_position, "end_y": length}
        else:
            first_data = np.ascontiguousarray(source.base_data[:, :split_position].copy())
            second_data = np.ascontiguousarray(source.base_data[:, split_position:].copy())
            first_bounds = {"axis": axis, "start_x": 0, "end_x": split_position}
            second_bounds = {"axis": axis, "start_x": split_position, "end_x": length}

        first_id = self._create_derived_core(
            source_core_id, source, first_data, first_name, "split", first_bounds, False
        )
        second_id = self._create_derived_core(
            source_core_id, source, second_data, second_name, "split", second_bounds, False
        )
        self._store.update_field(
            source_core_id,
            "child_core_ids",
            [*source.child_core_ids, first_id, second_id],
        )
        return first_id, second_id

    def create_cropped_child_core(
        self,
        parent_core_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        name: str | None = None,
    ) -> str | None:
        """Crop a rect from a core's *raw* base_data and create a child entity.

        The child's base_data is the unfiltered pixel slice — filters are
        inherited from the parent and applied at render time.  This means
        the child always renders identically to the same region on the parent.

        Args:
            parent_core_id: ID of the source parent core.
            x, y, w, h: Crop region in image-space pixels (clamped to image bounds).
            name: Optional explicit child name.

        Returns:
            The created child core id, or None if the parent is missing / has no data.
        """
        import numpy as np
        parent = self._store.get(parent_core_id)
        if not isinstance(parent, CoreEntity) or parent.base_data is None:
            logger.warning("create_cropped_child_core: parent '%s' has no base_data", parent_core_id)
            return None
        img_h, img_w = parent.base_data.shape[:2]
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        w = max(1, min(w, img_w - x))
        h = max(1, min(h, img_h - y))
        crop = parent.base_data[y:y + h, x:x + w, :].copy()
        return self.create_child_core(
            parent_core_id=parent_core_id,
            base_data=crop,
            name=name,
            derivation_type="crop",
            derivation_params={"x": x, "y": y, "w": w, "h": h},
            is_draft=False,
        )

    def set_core_mm_per_px(self, core_id: str, mm_per_px: float) -> None:
        """Update the spatial calibration scale for a core.

        Propagation to child cores is handled automatically by the Store via
        PROPAGATION_RULES in src/domain/entities/propagation.py.
        """
        self._store.update_field(core_id, "mm_per_px", mm_per_px)

    def set_core_illuminant(self, core_id: str, illuminant: str | None) -> None:
        """Update the capture illuminant for a core.

        Propagation to child cores is handled automatically by the Store via
        PROPAGATION_RULES in src/domain/entities/propagation.py.
        """
        logger.debug("[illuminant] setting core %s illuminant -> %r", core_id, illuminant)
        self._store.update_field(core_id, "illuminant", illuminant)

    def open_core_in_studio(self, core_id: str) -> None:
        """Open a CoreEntity in a CoreStudioPanel workspace tab."""
        if self._workspace_state is None:
            return
        panel_id = f"{_CORE_STUDIO_TAB_PREFIX}{core_id}"
        self._workspace_state.open(
            WorkspaceEntry(
                panel_id=panel_id,
                panel_type="CoreStudioPanel",
                target_entity_id=core_id,
            )
        )

    def open_blank_core_studio(self) -> None:
        """Open a single blank CoreStudioPanel tab.

        The blank panel is a workspace-level utility surface where users can
        drop/select an image to begin a new draft core workflow.
        """
        if self._workspace_state is None:
            return
        self._workspace_state.open(
            WorkspaceEntry(
                panel_id=_BLANK_CORE_STUDIO_PANEL_ID,
                panel_type="CoreStudioPanel",
                target_entity_id=None,
            )
        )

    def open_core_studio(self) -> None:
        """Open Core Studio for the currently active core, or the most recently added one."""
        if self._workspace_state is not None:
            active_id = self._workspace_state.active_entity_id
            if active_id is not None and isinstance(self._store.get(active_id), CoreEntity):
                self.open_core_in_studio(active_id)
                return
        cores = self._store.list_entities(entity_type="CoreEntity", include_ids=True)
        if cores:
            self.open_core_in_studio(cores[-1][0])
        else:
            self.open_blank_core_studio()

    def delete_entity(self, entity_id: str) -> object:
        """Remove an entity from the Store.

        If a DatasetEntity is deleted, any CoreEntity that references it via
        ``dataset_plots`` is updated to remove the stale entries first.

        Args:
            entity_id: The id of the entity to remove.

        Returns:
            The removed entity.
        """
        entity = self._store.get(entity_id)
        if isinstance(entity, DatasetEntity):
            for core_id, core in self._store.list_entities("CoreEntity", include_ids=True):
                clean = [p for p in core.dataset_plots if p.get("dataset_id") != entity_id]
                if len(clean) != len(core.dataset_plots):
                    core.dataset_plots = clean
                    self._store.update_field(core_id, "dataset_plots", clean)
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

    def set_dataset_depth_column(self, dataset_id: str, col_name: str | None) -> None:
        """Designate *col_name* as the depth axis for a DatasetEntity.

        Args:
            dataset_id: ID of the DatasetEntity.
            col_name: Column name whose values are depth in mm, or None to clear.
        """
        entity = self._store.get(dataset_id)
        if entity is None or not isinstance(entity, DatasetEntity):
            return
        entity.depth_column = col_name
        self._store.update_field(dataset_id, "depth_column", col_name)

    def set_dataset_plots(self, core_id: str, plots: list[dict]) -> None:
        """Replace the dataset plot list on a CoreEntity.

        Args:
            core_id: ID of the CoreEntity.
            plots: List of {dataset_id: str, column_name: str} dicts.
        """
        entity = self._store.get(core_id)
        if entity is None or not isinstance(entity, CoreEntity):
            return
        entity.dataset_plots = plots
        self._store.update_field(core_id, "dataset_plots", plots)

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
        # Cascade: update depth_column if it was the renamed column
        if entity.depth_column == old_name:
            entity.depth_column = new_name
            self._store.update_field(entity_id, "depth_column", new_name)
        self._store.update_field(entity_id, "data", entity.data)
        # Cascade: update any CoreEntity dataset_plots that reference the old col name
        for core_id, core in self._store.list_entities("CoreEntity", include_ids=True):
            updated = False
            for p in core.dataset_plots:
                if p.get("dataset_id") == entity_id and p.get("column_name") == old_name:
                    p["column_name"] = new_name
                    updated = True
            if updated:
                self._store.update_field(core_id, "dataset_plots", core.dataset_plots)

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

    def create_blank_dataset(self) -> str:
        """Create an empty DatasetEntity, auto-name it, and open it in the workspace.

        Returns:
            The entity id assigned by the Store.
        """
        import pandas as pd
        existing = self._store.list_entities("DatasetEntity")
        name = f"Dataset {len(existing) + 1}"
        entity = DatasetEntity(
            name=name,
            data=pd.DataFrame(),
            columns=[],
            column_types={},
        )
        entity_id = self._store.add(entity)
        if self._workspace_state is not None:
            from src.application.services import workspace_service
            try:
                workspace_service.open_entity(entity_id, self._store, self._workspace_state)
            except ValueError as e:
                logger.warning("create_blank_dataset: %s", e)
        return entity_id

    def add_dataset_column(self, entity_id: str) -> None:
        """Append an auto-named Text column to a DatasetEntity."""
        import pandas as pd
        entity = self._store.get(entity_id)
        if entity is None or not isinstance(entity, DatasetEntity):
            return
        if entity.data is None:
            entity.data = pd.DataFrame()
        col_name = f"Column {len(entity.columns) + 1}"
        while col_name in entity.columns:
            col_name = f"Column {len(entity.columns) + len(entity.data.columns) + 1}"
        entity.data[col_name] = pd.Series([None] * len(entity.data), dtype=object)
        entity.columns = list(entity.data.columns)
        entity.column_types[col_name] = "Text"
        self._store.update_field(entity_id, "data", entity.data)

    def remove_dataset_column(self, entity_id: str, col_name: str) -> None:
        """Remove a column from a DatasetEntity, cascading to depth_column and dataset_plots."""
        entity = self._store.get(entity_id)
        if entity is None or not isinstance(entity, DatasetEntity) or entity.data is None:
            return
        if col_name not in entity.data.columns:
            return
        entity.data = entity.data.drop(columns=[col_name])
        entity.columns = list(entity.data.columns)
        entity.column_types.pop(col_name, None)
        if entity.depth_column == col_name:
            entity.depth_column = None
            self._store.update_field(entity_id, "depth_column", None)
        self._store.update_field(entity_id, "data", entity.data)
        # Clean stale dataset_plots refs in all cores
        for core_id, core in self._store.list_entities("CoreEntity", include_ids=True):
            clean = [
                p for p in core.dataset_plots
                if not (p.get("dataset_id") == entity_id and p.get("column_name") == col_name)
            ]
            if len(clean) != len(core.dataset_plots):
                core.dataset_plots = clean
                self._store.update_field(core_id, "dataset_plots", clean)

    def add_dataset_row(self, entity_id: str) -> None:
        """Append a blank row to a DatasetEntity."""
        import pandas as pd
        entity = self._store.get(entity_id)
        if entity is None or not isinstance(entity, DatasetEntity):
            return
        if entity.data is None:
            entity.data = pd.DataFrame()
        blank = {col: None for col in entity.data.columns}
        entity.data = pd.concat(
            [entity.data, pd.DataFrame([blank])], ignore_index=True
        )
        self._store.update_field(entity_id, "data", entity.data)

    def remove_dataset_row(self, entity_id: str, row_index: int) -> None:
        """Remove a row from a DatasetEntity by its 0-based integer position."""
        entity = self._store.get(entity_id)
        if entity is None or not isinstance(entity, DatasetEntity) or entity.data is None:
            return
        if row_index < 0 or row_index >= len(entity.data):
            return
        entity.data = (
            entity.data
            .drop(index=entity.data.index[row_index])
            .reset_index(drop=True)
        )
        self._store.update_field(entity_id, "data", entity.data)

    def paste_dataset_data(
        self,
        entity_id: str,
        start_row: int,
        start_col: int,
        rows: list[list[str]],
    ) -> None:
        """Paste a 2-D block of string values into a DatasetEntity.

        Auto-creates columns and rows as needed so the paste area always fits.
        One ``entityUpdated`` signal is emitted at the end (not per-cell).

        Args:
            entity_id: ID of the DatasetEntity.
            start_row: 0-based row of the top-left paste anchor.
            start_col: 0-based column of the top-left paste anchor.
            rows: 2-D list of string values (row-major).
        """
        import pandas as pd
        entity = self._store.get(entity_id)
        if entity is None or not isinstance(entity, DatasetEntity):
            return
        if entity.data is None:
            entity.data = pd.DataFrame()
        if not rows:
            return

        needed_cols = start_col + max(len(r) for r in rows)
        needed_rows = start_row + len(rows)

        # Expand columns if needed
        while len(entity.columns) < needed_cols:
            col_name = f"Column {len(entity.columns) + 1}"
            entity.data[col_name] = pd.Series([None] * len(entity.data), dtype=object)
            entity.columns = list(entity.data.columns)
            entity.column_types[col_name] = "Text"

        # Expand rows if needed
        while len(entity.data) < needed_rows:
            blank = {col: None for col in entity.data.columns}
            entity.data = pd.concat(
                [entity.data, pd.DataFrame([blank])], ignore_index=True
            )

        # Fill cells
        for r_offset, row in enumerate(rows):
            for c_offset, value in enumerate(row):
                abs_row = start_row + r_offset
                abs_col = start_col + c_offset
                if abs_col >= len(entity.columns):
                    continue
                entity.data.iloc[abs_row, abs_col] = value if value != "" else None

        entity.columns = list(entity.data.columns)
        self._store.update_field(entity_id, "data", entity.data)

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
            if isinstance(entity, CoreEntity) and entity.asset_ref:
                try:
                    entity.base_data = iio.imread(entity.asset_ref)
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