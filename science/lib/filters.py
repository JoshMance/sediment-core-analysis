"""Image filter transforms — pure ndarray → ndarray science functions.

Each function takes an (H, W, 3) uint8 RGB array and a float parameter,
and returns a transformed (H, W, 3) uint8 RGB array.

Dispatch logic (registries, stack iteration, enabled flags) lives in the
application layer (``src/application/services/resolve_image.py``), not here.
"""
from __future__ import annotations

import numpy as np

_MAX = 255.0


def _f(arr: np.ndarray) -> np.ndarray:
    """uint8 → float32 in [0, 1]."""
    return arr.astype(np.float32) / _MAX


def _u8(arr: np.ndarray) -> np.ndarray:
    """float32 → uint8, clipped."""
    return np.clip(arr * _MAX, 0.0, _MAX).astype(np.uint8)


def brightness(arr: np.ndarray, value: float) -> np.ndarray:
    """Multiply every channel by *value*. 1.0 = identity, >1 brightens."""
    return _u8(_f(arr) * float(value))


def contrast(arr: np.ndarray, value: float) -> np.ndarray:
    """Scale contrast around the 0.5 midpoint. 1.0 = identity."""
    return _u8((_f(arr) - 0.5) * float(value) + 0.5)


def gamma(arr: np.ndarray, value: float) -> np.ndarray:
    """Power-curve gamma correction. 1.0 = identity; <1 brightens, >1 darkens."""
    v = max(float(value), 1e-6)
    return _u8(np.power(_f(arr), v))
