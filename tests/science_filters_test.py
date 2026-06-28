"""Unit tests for science.lib.filters — pure ndarray → ndarray transforms."""
from __future__ import annotations

import numpy as np
import pytest

from science.lib.filters import (
    brightness,
    contrast,
    gamma,
)
from src.application.services.resolve_image import FILTER_REGISTRY, resolve as apply_filter_stack


def _grey(value: int = 128, shape: tuple[int, int, int] = (4, 4, 3)) -> np.ndarray:
    """Return a solid-colour uint8 image."""
    return np.full(shape, value, dtype=np.uint8)


# ── Individual filter functions ────────────────────────────────────────────────


class TestBrightness:
    def test_identity(self) -> None:
        arr = _grey(100)
        result = brightness(arr, 1.0)
        assert np.array_equal(result, arr)

    def test_doubles(self) -> None:
        arr = _grey(100)
        result = brightness(arr, 2.0)
        assert np.all(result == 200)

    def test_clamps_at_255(self) -> None:
        arr = _grey(200)
        result = brightness(arr, 2.0)
        assert np.all(result == 255)

    def test_zero_gives_black(self) -> None:
        arr = _grey(200)
        result = brightness(arr, 0.0)
        assert np.all(result == 0)

    def test_preserves_dtype(self) -> None:
        arr = _grey(128)
        assert brightness(arr, 1.5).dtype == np.uint8


class TestContrast:
    def test_identity(self) -> None:
        arr = _grey(128)
        result = contrast(arr, 1.0)
        assert np.array_equal(result, arr)

    def test_zero_gives_midgrey(self) -> None:
        arr = _grey(200)
        result = contrast(arr, 0.0)
        # 0.5 * 255 = 127.5, truncated to uint8 → 127
        assert np.all(result == 127)

    def test_higher_contrast_darkens_dark_pixels(self) -> None:
        arr = _grey(64)
        result = contrast(arr, 2.0)
        # 128 + (64 - 128) * 2 = 128 - 128 = 0
        assert np.all(result == 0)

    def test_higher_contrast_brightens_bright_pixels(self) -> None:
        arr = _grey(192)
        result = contrast(arr, 2.0)
        # 128 + (192 - 128) * 2 = 128 + 128 = 256 → clamped 255
        assert np.all(result == 255)

    def test_preserves_dtype(self) -> None:
        arr = _grey(128)
        assert contrast(arr, 1.5).dtype == np.uint8


class TestGamma:
    def test_identity(self) -> None:
        arr = _grey(128)
        result = gamma(arr, 1.0)
        assert np.array_equal(result, arr)

    def test_brightens_with_gamma_less_than_one(self) -> None:
        arr = _grey(128)
        result = gamma(arr, 0.5)
        # x^0.5 with x = 128/255 → result > 128/255 → scaled > 128
        # float32 arithmetic floors on uint8 cast — just assert direction
        assert np.all(result > 128)

    def test_darkens_with_gamma_greater_than_one(self) -> None:
        arr = _grey(128)
        result = gamma(arr, 2.0)
        expected_val = round((128 / 255) ** 2.0 * 255)
        assert np.all(result == expected_val)

    def test_black_stays_black(self) -> None:
        assert np.all(gamma(_grey(0), 0.5) == 0)

    def test_white_stays_white(self) -> None:
        assert np.all(gamma(_grey(255), 2.0) == 255)

    def test_preserves_dtype(self) -> None:
        arr = _grey(128)
        assert gamma(arr, 0.5).dtype == np.uint8


# ── apply_filter_stack ─────────────────────────────────────────────────────────


class TestApplyFilterStack:
    def test_empty_stack_returns_input_unchanged(self) -> None:
        arr = _grey(100)
        result = apply_filter_stack(arr, [])
        assert np.array_equal(result, arr)

    def test_single_filter_applied(self) -> None:
        arr = _grey(100)
        stack = [{"type": "brightness", "value": 2.0, "enabled": True}]
        result = apply_filter_stack(arr, stack)
        assert np.all(result == 200)

    def test_disabled_filter_is_skipped(self) -> None:
        arr = _grey(100)
        stack = [{"type": "brightness", "value": 2.0, "enabled": False}]
        result = apply_filter_stack(arr, stack)
        assert np.array_equal(result, arr)

    def test_enabled_defaults_to_true(self) -> None:
        arr = _grey(100)
        stack = [{"type": "brightness", "value": 2.0}]  # no "enabled" key
        result = apply_filter_stack(arr, stack)
        assert np.all(result == 200)

    def test_chain_of_two_filters(self) -> None:
        arr = _grey(100)
        # brightness × 2 → 200, then brightness × 0.5 → 100
        stack = [
            {"type": "brightness", "value": 2.0, "enabled": True},
            {"type": "brightness", "value": 0.5, "enabled": True},
        ]
        result = apply_filter_stack(arr, stack)
        assert np.all(result == 100)

    def test_unknown_type_is_silently_skipped(self) -> None:
        arr = _grey(100)
        stack = [{"type": "nonexistent_filter", "value": 5.0, "enabled": True}]
        result = apply_filter_stack(arr, stack)
        assert np.array_equal(result, arr)

    def test_mix_of_enabled_and_disabled(self) -> None:
        arr = _grey(100)
        stack = [
            {"type": "brightness", "value": 2.0, "enabled": True},
            {"type": "brightness", "value": 2.0, "enabled": False},
        ]
        result = apply_filter_stack(arr, stack)
        assert np.all(result == 200)

    def test_does_not_mutate_input(self) -> None:
        arr = _grey(100)
        original = arr.copy()
        apply_filter_stack(arr, [{"type": "brightness", "value": 2.0}])
        assert np.array_equal(arr, original)


# ── FILTER_REGISTRY ────────────────────────────────────────────────────────────


def test_registry_contains_all_standard_filters() -> None:
    for key in ("brightness", "contrast", "gamma"):
        assert key in FILTER_REGISTRY, f"Expected '{key}' in FILTER_REGISTRY"


def test_registry_callables_are_correct() -> None:
    assert FILTER_REGISTRY["brightness"] is brightness
    assert FILTER_REGISTRY["contrast"] is contrast
    assert FILTER_REGISTRY["gamma"] is gamma
