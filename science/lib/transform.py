"""Colour-space conversion functions for RGB, XYZ, and CIELAB.

Public API (first slice):

- rgb_to_cielab
- cielab_to_rgb
- rgb_to_xyz
- xyz_to_rgb
- cielab_to_xyz
- xyz_to_cielab

Input policy for RGB:

- Integer RGB is accepted and scaled by dtype max (e.g. uint8 0..255, uint16 0..65535).
- Float RGB is accepted in either 0..1 or 0..255 (auto-normalized to 0..1).
- RGB arrays must have a final channel dimension of size 3.

Output policy for *_to_rgb:

- Always returns uint8 RGB in 0..255.
- Out-of-gamut RGB is clipped before uint8 conversion.

XYZ contract:

- XYZ values are in relative scale where white has Y=1.0, matching the
    active colorimetry profile in science/data/colorimetry.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

_COLORIMETRY_PATH = (
    pathlib.Path(__file__).parent.parent
    / "data"
    / "colorimetry"
    / "srgb_d65_2deg.json"
)


@dataclass(frozen=True)
class _ColorimetrySpec:
    """Runtime colorimetry constants loaded from module data."""

    schema_version: int
    name: str
    source: str
    illuminant: str
    observer_degrees: int
    white_point_xyz: np.ndarray
    rgb_to_xyz: np.ndarray
    xyz_to_rgb: np.ndarray


@lru_cache(maxsize=1)
def _colorimetry_spec() -> _ColorimetrySpec:
    """Load and validate colorimetry constants from JSON data."""
    raw = json.loads(_COLORIMETRY_PATH.read_text(encoding="utf-8"))

    required = {
        "schema_version",
        "name",
        "source",
        "illuminant",
        "observer_degrees",
        "white_point_xyz",
        "rgb_to_xyz",
        "xyz_to_rgb",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(
            f"Colorimetry spec is missing required keys: {missing}"
        )

    schema_version = int(raw["schema_version"])
    if schema_version != 1:
        raise ValueError(
            f"Unsupported colorimetry schema_version={schema_version}; expected 1"
        )

    name = str(raw["name"])
    source = str(raw["source"])
    illuminant = str(raw["illuminant"])
    observer_degrees = int(raw["observer_degrees"])

    white = np.asarray(raw["white_point_xyz"], dtype=np.float64)
    rgb_to_xyz = np.asarray(raw["rgb_to_xyz"], dtype=np.float64)
    xyz_to_rgb = np.asarray(raw["xyz_to_rgb"], dtype=np.float64)

    if white.shape != (3,):
        raise ValueError("white_point_xyz must have exactly 3 values")
    if rgb_to_xyz.shape != (3, 3):
        raise ValueError("rgb_to_xyz must be a 3x3 matrix")
    if xyz_to_rgb.shape != (3, 3):
        raise ValueError("xyz_to_rgb must be a 3x3 matrix")

    return _ColorimetrySpec(
        schema_version=schema_version,
        name=name,
        source=source,
        illuminant=illuminant,
        observer_degrees=observer_degrees,
        white_point_xyz=white,
        rgb_to_xyz=rgb_to_xyz,
        xyz_to_rgb=xyz_to_rgb,
    )


def _require_3_channels(array: np.ndarray, name: str) -> np.ndarray:
    """Require an array with a trailing channel dimension of size 3."""
    arr = np.asarray(array)
    if arr.ndim < 1 or arr.shape[-1] != 3:
        raise ValueError(f"{name} must have a final channel dimension of size 3")
    return arr


def _srgb_to_linear(rgb01: np.ndarray) -> np.ndarray:
    """Apply inverse sRGB transfer function to rgb in 0..1."""
    threshold = 0.04045
    return np.where(
        rgb01 <= threshold,
        rgb01 / 12.92,
        ((rgb01 + 0.055) / 1.055) ** 2.4,
    )


def _linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Apply forward sRGB transfer function to linear-light rgb."""
    threshold = 0.0031308
    return np.where(
        linear <= threshold,
        12.92 * linear,
        1.055 * np.power(np.clip(linear, 0.0, None), 1.0 / 2.4) - 0.055,
    )


def _to_rgb01(rgb: np.ndarray) -> np.ndarray:
    """Normalize supported RGB inputs to float64 in 0..1."""
    arr = _require_3_channels(rgb, "rgb")

    if np.issubdtype(arr.dtype, np.integer):
        info = np.iinfo(arr.dtype)
        if info.min < 0:
            raise ValueError("Signed integer RGB is not supported")
        return arr.astype(np.float64) / float(info.max)

    if np.issubdtype(arr.dtype, np.floating):
        if not np.all(np.isfinite(arr)):
            raise ValueError("RGB float input must be finite")

        min_v = float(np.min(arr))
        max_v = float(np.max(arr))
        if min_v < 0.0:
            raise ValueError("RGB float input cannot contain negatives")

        # Accept float RGB in either 0..1 or 0..255.
        if max_v <= 1.0:
            return arr.astype(np.float64)
        if max_v <= 255.0:
            return arr.astype(np.float64) / 255.0
        raise ValueError("RGB float input must be in 0..1 or 0..255")

    raise ValueError("RGB input must be integer or float")


def _rgb01_to_uint8(rgb01: np.ndarray) -> np.ndarray:
    """Convert rgb in 0..1 to uint8 with clip and round policy."""
    clipped = np.clip(rgb01, 0.0, 1.0)
    return np.rint(clipped * 255.0).astype(np.uint8)


def _lab_forward(ratio: np.ndarray) -> np.ndarray:
    """CIE f(t) helper used in XYZ -> CIELAB."""
    delta = 6.0 / 29.0
    delta3 = delta ** 3
    return np.where(
        ratio > delta3,
        np.cbrt(ratio),
        (ratio / (3.0 * delta * delta)) + (4.0 / 29.0),
    )


def _lab_inverse(f_component: np.ndarray) -> np.ndarray:
    """CIE f^-1(t) helper used in CIELAB -> XYZ."""
    delta = 6.0 / 29.0
    return np.where(
        f_component > delta,
        f_component ** 3,
        3.0 * delta * delta * (f_component - (4.0 / 29.0)),
    )


def rgb_to_xyz(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB to CIE XYZ using the active colorimetry profile.

    Accepts int or float RGB. Returns float32 XYZ.
    """
    spec = _colorimetry_spec()
    rgb01 = _to_rgb01(rgb)
    linear = _srgb_to_linear(rgb01)
    xyz = np.tensordot(linear, spec.rgb_to_xyz.T, axes=([-1], [0]))
    return xyz.astype(np.float32)


def xyz_to_rgb(xyz: np.ndarray) -> np.ndarray:
    """Convert CIE XYZ to RGB uint8 in 0..255 using active profile.

    Values outside displayable RGB gamut are clipped before uint8 output.
    """
    spec = _colorimetry_spec()
    arr = _require_3_channels(xyz, "xyz").astype(np.float64)
    linear = np.tensordot(arr, spec.xyz_to_rgb.T, axes=([-1], [0]))
    srgb01 = _linear_to_srgb(linear)
    return _rgb01_to_uint8(srgb01)


def xyz_to_cielab(xyz: np.ndarray) -> np.ndarray:
    """Convert CIE XYZ to CIELAB using active profile white point."""
    spec = _colorimetry_spec()
    arr = _require_3_channels(xyz, "xyz").astype(np.float64)
    ratio = arr / spec.white_point_xyz
    f = _lab_forward(ratio)

    l = (116.0 * f[..., 1]) - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])
    lab = np.stack([l, a, b], axis=-1)
    return lab.astype(np.float32)


def cielab_to_xyz(cielab: np.ndarray) -> np.ndarray:
    """Convert CIELAB to CIE XYZ using active profile white point."""
    spec = _colorimetry_spec()
    lab = _require_3_channels(cielab, "cielab").astype(np.float64)
    l = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    fy = (l + 16.0) / 116.0
    fx = fy + (a / 500.0)
    fz = fy - (b / 200.0)

    xyz_ratio = np.stack(
        [_lab_inverse(fx), _lab_inverse(fy), _lab_inverse(fz)],
        axis=-1,
    )

    xyz = xyz_ratio * spec.white_point_xyz
    return xyz.astype(np.float32)


def rgb_to_cielab(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB to CIELAB using the active colorimetry profile."""
    return xyz_to_cielab(rgb_to_xyz(rgb))


def cielab_to_rgb(cielab: np.ndarray) -> np.ndarray:
    """Convert CIELAB to RGB uint8 in 0..255."""
    return xyz_to_rgb(cielab_to_xyz(cielab))


__all__ = [
    "rgb_to_cielab",
    "cielab_to_rgb",
    "rgb_to_xyz",
    "xyz_to_rgb",
    "cielab_to_xyz",
    "xyz_to_cielab",
]
