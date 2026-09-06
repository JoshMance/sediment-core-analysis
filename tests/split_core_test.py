"""Tests for non-destructive core splitting."""
from __future__ import annotations

import numpy as np

from src.application import AppController
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store


def test_split_core_creates_two_calibrated_children() -> None:
    store = Store()
    controller = AppController(store)
    source_data = np.arange(6 * 4 * 3, dtype=np.uint8).reshape(6, 4, 3)
    source_id = controller.create_core_entity(
        name="Source",
        base_data=source_data,
        mm_per_px=0.25,
        filter_stack=[{"name": "contrast", "value": 1.2}],
    )
    controller.set_core_illuminant(source_id, "D65")

    result = controller.split_core(source_id, "horizontal", 2, "Upper", "Lower")

    assert result is not None
    upper_id, lower_id = result
    source = store.get(source_id)
    upper = store.get(upper_id)
    lower = store.get(lower_id)
    assert isinstance(source, CoreEntity)
    assert isinstance(upper, CoreEntity)
    assert isinstance(lower, CoreEntity)
    assert np.array_equal(source.base_data, source_data)
    assert np.array_equal(upper.base_data, source_data[:2])
    assert np.array_equal(lower.base_data, source_data[2:])
    assert (upper.parent_core_id, lower.parent_core_id) == (source_id, source_id)
    assert source.child_core_ids == [upper_id, lower_id]
    assert upper.mm_per_px == lower.mm_per_px == 0.25
    assert upper.illuminant == lower.illuminant == "D65"
    assert upper.filter_stack == lower.filter_stack == source.filter_stack
    assert upper.filter_stack is not source.filter_stack
    assert upper.derivation_params == {"axis": "horizontal", "start_y": 0, "end_y": 2}
    assert lower.derivation_params == {"axis": "horizontal", "start_y": 2, "end_y": 6}


def test_split_core_rejects_edge_cut_without_mutation() -> None:
    store = Store()
    controller = AppController(store)
    source_id = controller.create_core_entity(
        name="Source", base_data=np.zeros((4, 2, 3), dtype=np.uint8)
    )

    assert controller.split_core(source_id, "horizontal", 0, "Upper", "Lower") is None
    assert store.count("CoreEntity") == 1


def test_split_core_vertically_creates_left_and_right_children() -> None:
    store = Store()
    controller = AppController(store)
    source_data = np.arange(3 * 6 * 3, dtype=np.uint8).reshape(3, 6, 3)
    source_id = controller.create_core_entity(name="Source", base_data=source_data)

    result = controller.split_core(source_id, "vertical", 2, "Left", "Right")

    assert result is not None
    left_id, right_id = result
    left = store.get(left_id)
    right = store.get(right_id)
    assert isinstance(left, CoreEntity)
    assert isinstance(right, CoreEntity)
    assert np.array_equal(left.base_data, source_data[:, :2])
    assert np.array_equal(right.base_data, source_data[:, 2:])
    assert left.derivation_params == {"axis": "vertical", "start_x": 0, "end_x": 2}
    assert right.derivation_params == {"axis": "vertical", "start_x": 2, "end_x": 6}


def test_split_core_round_trips_through_session_archive(tmp_path) -> None:
    store = Store()
    controller = AppController(store)
    source_data = np.arange(6 * 2 * 3, dtype=np.uint8).reshape(6, 2, 3)
    source_id = controller.create_core_entity(name="Source", base_data=source_data)
    result = controller.split_core(source_id, "horizontal", 3, "Upper", "Lower")

    assert result is not None
    upper_id, lower_id = result
    archive_path = tmp_path / "split.sedivis"
    controller.save_session(archive_path)
    controller.new_session()
    controller.load_session(archive_path)

    source = store.get(source_id)
    upper = store.get(upper_id)
    lower = store.get(lower_id)
    assert isinstance(source, CoreEntity)
    assert isinstance(upper, CoreEntity)
    assert isinstance(lower, CoreEntity)
    assert source.child_core_ids == [upper_id, lower_id]
    assert upper.parent_core_id == lower.parent_core_id == source_id
    assert np.array_equal(upper.base_data, source_data[:3])
    assert np.array_equal(lower.base_data, source_data[3:])