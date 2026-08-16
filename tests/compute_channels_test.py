from __future__ import annotations

import numpy as np

from science.lib import rgb_to_cielab
from src.application.services import compute_channels


def test_for_core_returns_rgb_and_lab_profiles_without_rotation() -> None:
    image = np.array(
        [
            [[10, 20, 30], [30, 40, 50]],
            [[70, 80, 90], [90, 100, 110]],
        ],
        dtype=np.uint8,
    )

    out = compute_channels.for_core(image, "D65")

    expected_rgb = image.astype(np.float32).mean(axis=1)
    expected_lab = rgb_to_cielab(expected_rgb, "D65")

    assert np.allclose(out.r, expected_rgb[:, 0])
    assert np.allclose(out.g, expected_rgb[:, 1])
    assert np.allclose(out.b, expected_rgb[:, 2])
    assert np.allclose(out.l_star, expected_lab[:, 0])
    assert np.allclose(out.a_star, expected_lab[:, 1])
    assert np.allclose(out.b_star, expected_lab[:, 2])


def test_for_core_rotates_landscape_to_match_core_studio_orientation() -> None:
    image = np.array(
        [
            [[10, 10, 10], [20, 20, 20], [30, 30, 30]],
            [[40, 40, 40], [50, 50, 50], [60, 60, 60]],
        ],
        dtype=np.uint8,
    )

    out = compute_channels.for_core(image, "D65")

    oriented = np.rot90(image)
    expected_rgb = oriented.astype(np.float32).mean(axis=1)

    assert out.r.shape[0] == oriented.shape[0]
    assert np.allclose(out.r, expected_rgb[:, 0])
    assert np.allclose(out.g, expected_rgb[:, 1])
    assert np.allclose(out.b, expected_rgb[:, 2])
