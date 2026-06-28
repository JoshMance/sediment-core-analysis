"""Automated Gate 5 validation for core-only migration."""

from __future__ import annotations

from pathlib import Path

import imageio.v3 as iio
import numpy as np

from src.application import AppController
from src.application.workspace_state import WorkspaceState
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store


def _write_test_png(path: Path) -> np.ndarray:
    data = np.array(
        [
            [[0, 0, 0], [255, 255, 255], [10, 20, 30]],
            [[5, 6, 7], [40, 50, 60], [200, 120, 20]],
        ],
        dtype=np.uint8,
    )
    iio.imwrite(path, data)
    return data


def test_import_image_creates_core_entity(tmp_path: Path) -> None:
    store = Store()
    controller = AppController(store)

    image_path = tmp_path / "import.png"
    expected = _write_test_png(image_path)

    core_id = controller.import_core_from_image(str(image_path))

    assert core_id is not None
    entity = store.get(core_id)
    assert isinstance(entity, CoreEntity)
    assert entity.derivation_type == "import"
    assert entity.source_file_path == image_path
    assert entity.base_data is not None
    assert entity.base_data.shape == expected.shape


def test_create_child_core_preserves_lineage(tmp_path: Path) -> None:
    store = Store()
    controller = AppController(store)

    parent_data = np.full((4, 4, 3), 100, dtype=np.uint8)
    parent_id = controller.create_core_entity(
        name="parent",
        base_data=parent_data,
        source_file_path=tmp_path / "parent.png",
        derivation_type="import",
        derivation_params={},
        is_draft=False,
    )

    child_data = np.full((2, 2, 3), 25, dtype=np.uint8)
    child_id = controller.create_child_core(
        parent_core_id=parent_id,
        base_data=child_data,
        derivation_type="crop",
        derivation_params={"x": 1, "y": 1, "w": 2, "h": 2},
        is_draft=False,
    )

    assert child_id is not None
    parent = store.get(parent_id)
    child = store.get(child_id)

    assert isinstance(parent, CoreEntity)
    assert isinstance(child, CoreEntity)
    assert child.parent_core_id == parent_id
    assert child.derivation_type == "crop"
    assert child_id in parent.child_core_ids


def test_open_in_workspace_maps_core_to_core_image_panel() -> None:
    store = Store()
    workspace_state = WorkspaceState()
    controller = AppController(store, workspace_state=workspace_state)

    core_id = controller.create_core_entity(
        name="openable-core",
        base_data=np.zeros((2, 2, 3), dtype=np.uint8),
        derivation_type="import",
        derivation_params={},
    )

    controller.open_in_workspace(core_id)

    panel_id = f"core_image::{core_id}"
    assert workspace_state.is_open(panel_id)
    assert workspace_state._entries[panel_id].panel_type == "CoreImagePanel"
    assert workspace_state._entries[panel_id].target_entity_id == core_id


def test_core_studio_opens_alongside_core_image_panel() -> None:
    store = Store()
    workspace_state = WorkspaceState()
    controller = AppController(store, workspace_state=workspace_state)

    core_id = controller.create_core_entity(
        name="studio-openable-core",
        base_data=np.zeros((2, 2, 3), dtype=np.uint8),
        derivation_type="import",
        derivation_params={},
    )

    controller.open_in_workspace(core_id)
    controller.open_core_in_studio(core_id)

    image_panel_id = f"core_image::{core_id}"
    studio_panel_id = f"core_studio::{core_id}"
    assert workspace_state.is_open(image_panel_id)
    assert workspace_state._entries[image_panel_id].panel_type == "CoreImagePanel"
    assert workspace_state.is_open(studio_panel_id)
    assert workspace_state._entries[studio_panel_id].panel_type == "CoreStudioPanel"
    assert workspace_state._entries[studio_panel_id].target_entity_id == core_id


def test_session_save_load_round_trip_core_and_workspace(tmp_path: Path) -> None:
    store = Store()
    workspace_state = WorkspaceState()
    controller = AppController(store, workspace_state=workspace_state)

    image_path = tmp_path / "session_input.png"
    expected = _write_test_png(image_path)
    core_id = controller.import_core_from_image(str(image_path))
    assert core_id is not None

    controller.open_in_workspace(core_id)

    archive_path = tmp_path / "round_trip.sedivis"
    controller.save_session(archive_path)
    controller.new_session()

    assert store.count() == 0
    assert not workspace_state.is_open(f"core_image::{core_id}")

    controller.load_session(archive_path)

    loaded_core = store.get(core_id)
    assert isinstance(loaded_core, CoreEntity)
    assert loaded_core.base_data is not None
    assert loaded_core.base_data.shape == expected.shape
    assert np.array_equal(loaded_core.base_data, expected)
    image_panel_id = f"core_image::{core_id}"
    assert workspace_state.is_open(image_panel_id)
    assert workspace_state._entries[image_panel_id].panel_type == "CoreImagePanel"
    assert workspace_state._entries[image_panel_id].target_entity_id == core_id


def test_delete_entity_closes_targeted_panels() -> None:
    store = Store()
    workspace_state = WorkspaceState(store)
    controller = AppController(store, workspace_state=workspace_state)

    core_id = controller.create_core_entity(
        name="delete-me-core",
        base_data=np.zeros((2, 2, 3), dtype=np.uint8),
        derivation_type="import",
        derivation_params={},
    )

    controller.open_in_workspace(core_id)
    controller.open_core_in_studio(core_id)

    image_panel_id = f"core_image::{core_id}"
    studio_panel_id = f"core_studio::{core_id}"
    assert workspace_state.is_open(image_panel_id)
    assert workspace_state.is_open(studio_panel_id)

    controller.delete_entity(core_id)

    assert not workspace_state.is_open(image_panel_id)
    assert not workspace_state.is_open(studio_panel_id)
