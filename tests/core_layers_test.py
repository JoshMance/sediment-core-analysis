"""Tests for Core Studio division and layer domain behavior."""
from __future__ import annotations

import numpy as np

from src.application import AppController
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store


def test_divisions_create_merge_and_serialize_layer_intervals(tmp_path) -> None:
    store = Store()
    controller = AppController(store)
    core_id = controller.create_core_entity("Core", np.zeros((100, 10, 3), dtype=np.uint8))

    controller.add_core_division(core_id, 30)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert len(core.divisions) == len(core.layers) - 1 == 1
    controller.update_core_layer(core_id, core.layers[0].id, "Upper", "Note")
    controller.add_core_division(core_id, 60)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert [division.position_px for division in core.divisions] == [30, 60]
    assert core.layers[0].title == "Upper"
    archive = tmp_path / "layers.sedivis"
    controller.save_session(archive)
    controller.new_session()
    controller.load_session(archive)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert core.layers[0].note == "Note"
    controller.remove_core_division(core_id, core.divisions[0].id)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert len(core.divisions) == 1 and len(core.layers) == 2
    assert core.layers[0].title == "Upper"


def test_insert_and_delete_layer_preserve_intended_neighbor_metadata() -> None:
    store = Store()
    controller = AppController(store)
    core_id = controller.create_core_entity("Core", np.zeros((100, 10, 3), dtype=np.uint8))
    controller.add_core_division(core_id, 50)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    controller.update_core_layer(core_id, core.layers[0].id, "Clay", "Upper note")
    controller.update_core_layer(core_id, core.layers[1].id, "Sand", "Lower note")

    controller.insert_core_layer(core_id, core.layers[0].id, above=True)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert [layer.title for layer in core.layers] == ["", "Clay", "Sand"]
    controller.delete_core_layer(core_id, core.layers[1].id)
    core = store.get(core_id)
    assert isinstance(core, CoreEntity)
    assert [layer.title for layer in core.layers] == ["", "Sand"]