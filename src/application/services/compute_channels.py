"""Application service for deriving Core Studio colour channels from core image data."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from science.lib import rgb_to_cielab


@dataclass(frozen=True)
class ChannelProfiles:
    """Row-wise channel profiles used by Core Studio columns."""

    r: np.ndarray
    g: np.ndarray
    b: np.ndarray
    l_star: np.ndarray
    a_star: np.ndarray
    b_star: np.ndarray


def for_core(image: np.ndarray) -> ChannelProfiles:
    """Compute row-wise RGB and CIELAB channels for a core image.

    The Core Studio image column rotates landscape images to vertical display.
    Profiles follow that same orientation so depth alignment stays consistent.
    """
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Core image must be an (H, W, 3) RGB array")
    if arr.shape[0] == 0 or arr.shape[1] == 0:
        raise ValueError("Core image must have non-zero height and width")

    oriented = np.rot90(arr) if arr.shape[1] > arr.shape[0] else arr
    row_rgb = oriented.astype(np.float32).mean(axis=1)
    row_lab = rgb_to_cielab(row_rgb).astype(np.float32)

    return ChannelProfiles(
        r=row_rgb[:, 0],
        g=row_rgb[:, 1],
        b=row_rgb[:, 2],
        l_star=row_lab[:, 0],
        a_star=row_lab[:, 1],
        b_star=row_lab[:, 2],
    )
