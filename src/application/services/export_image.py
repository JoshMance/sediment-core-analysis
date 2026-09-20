"""Image export for resolved core pixels."""
from __future__ import annotations

from pathlib import Path

import imageio.v3 as iio
import numpy as np


_SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg"}


def export_core(path: Path, data: np.ndarray) -> None:
    """Write resolved RGB core pixels to a PNG or JPEG file."""
    if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        raise ValueError("Image export supports PNG and JPEG files only.")
    iio.imwrite(path, data)