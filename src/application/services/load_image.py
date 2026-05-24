"""Image loader — pure I/O service

Reads an image file from disk and returns pixel data in the
format expected by a CoreEntity import flow. No signals, no Store
interaction, no domain logic.

Internal to the application layer (services/).
"""
from __future__ import annotations

from pathlib import Path

import imageio.v3 as iio

# Extensions recognised by the load pipeline (used by UI file filters)
IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
import numpy as np
from numpy.typing import NDArray


def load_image(path: str | Path) -> NDArray[np.uint8]:
    """Read an image file and return RGB pixel data.

    Args:
        path: Path to an image file (.png, .jpg, .jpeg, .tif, etc.)

    Returns:
        (H, W, 3) uint8 numpy array in RGB order.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be read as an image.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    try:
        data = iio.imread(path)
    except Exception as e:
        raise ValueError(f"Could not read image '{path.name}': {e}") from e

    # Handle grayscale → RGB
    if data.ndim == 2:
        data = np.stack([data, data, data], axis=-1)

    # Handle RGBA → RGB (drop alpha)
    if data.ndim == 3 and data.shape[2] == 4:
        data = data[:, :, :3]

    return data.astype(np.uint8)
