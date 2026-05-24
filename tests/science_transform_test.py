"""Deterministic tests for science.lib.transform conversion APIs."""

from __future__ import annotations

import numpy as np

from science.lib.transform import (
    cielab_to_rgb,
    cielab_to_xyz,
    rgb_to_cielab,
    rgb_to_xyz,
    xyz_to_cielab,
    xyz_to_rgb,
)


def test_rgb_to_cielab_accepts_uint8_and_float255_consistently() -> None:
    rgb_uint8 = np.array([[[10, 120, 250], [255, 0, 20]]], dtype=np.uint8)
    rgb_float255 = rgb_uint8.astype(np.float32)

    lab_a = rgb_to_cielab(rgb_uint8)
    lab_b = rgb_to_cielab(rgb_float255)

    assert lab_a.shape == rgb_uint8.shape
    assert lab_b.shape == rgb_uint8.shape
    assert np.allclose(lab_a, lab_b, atol=1e-4)


def test_rgb_xyz_round_trip_is_stable() -> None:
    rgb = np.array(
        [
            [[0, 0, 0], [255, 255, 255], [255, 0, 0]],
            [[0, 255, 0], [0, 0, 255], [12, 98, 201]],
        ],
        dtype=np.uint8,
    )
    xyz = rgb_to_xyz(rgb)
    rgb_back = xyz_to_rgb(xyz)

    assert rgb_back.dtype == np.uint8
    assert rgb_back.shape == rgb.shape
    assert np.max(np.abs(rgb_back.astype(np.int16) - rgb.astype(np.int16))) <= 1


def test_rgb_cielab_round_trip_is_stable() -> None:
    rgb = np.array(
        [
            [[20, 40, 60], [180, 120, 30]],
            [[255, 200, 10], [2, 6, 9]],
        ],
        dtype=np.uint8,
    )
    lab = rgb_to_cielab(rgb)
    rgb_back = cielab_to_rgb(lab)

    assert rgb_back.dtype == np.uint8
    assert rgb_back.shape == rgb.shape
    assert np.max(np.abs(rgb_back.astype(np.int16) - rgb.astype(np.int16))) <= 1


def test_xyz_cielab_round_trip_is_stable() -> None:
    xyz = np.array(
        [
            [[0.0, 0.0, 0.0], [0.95047, 1.0, 1.08883]],
            [[0.2, 0.3, 0.4], [0.05, 0.04, 0.03]],
        ],
        dtype=np.float32,
    )
    lab = xyz_to_cielab(xyz)
    xyz_back = cielab_to_xyz(lab)

    assert xyz_back.shape == xyz.shape
    assert np.allclose(xyz_back, xyz, atol=1e-4)
