"""Tests for Core Studio Excel measurement export."""
from __future__ import annotations

import numpy as np
from openpyxl import load_workbook

from src.application import AppController
from src.domain.store import Store


def test_calibrated_core_excel_export_includes_depth(tmp_path) -> None:
    store = Store()
    controller = AppController(store)
    core_id = controller.create_core_entity(
        name="Calibrated",
        base_data=np.array([[[10, 20, 30]], [[40, 50, 60]]], dtype=np.uint8),
        mm_per_px=0.5,
    )
    path = tmp_path / "calibrated.xlsx"

    controller.export_core_to_excel(core_id, path)

    workbook = load_workbook(path, data_only=True)
    data = workbook["Core data"]
    assert [cell.value for cell in data[1]] == [
        "image_row_px", "depth_mm", "R_mean", "G_mean", "B_mean", "L_star", "a_star", "b_star"
    ]
    assert data["A2"].value == 0
    assert data["B3"].value == 0.5
    assert [data["C2"].value, data["D2"].value, data["E2"].value] == [10, 20, 30]
    assert workbook.sheetnames == ["Core data"]


def test_uncalibrated_core_excel_export_omits_depth(tmp_path) -> None:
    store = Store()
    controller = AppController(store)
    core_id = controller.create_core_entity(
        name="Uncalibrated", base_data=np.zeros((2, 1, 3), dtype=np.uint8)
    )
    path = tmp_path / "uncalibrated.xlsx"

    controller.export_core_to_excel(core_id, path)

    workbook = load_workbook(path, data_only=True)
    data = workbook["Core data"]
    assert "depth_mm" not in [cell.value for cell in data[1]]
    assert workbook.sheetnames == ["Core data"]