"""Pipeline: Compute mean RGB per row of an image."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def mean_rgb_per_row(image: NDArray[np.uint8]) -> NDArray[np.float64]:
    """Compute mean RGB values for each row of an image.
    
    This is a pipeline that orchestrates array operations to compute
    per-row averages. It handles the array structure (H, W, 3) and
    aggregation logic.
    
    Args:
        image: (H, W, 3) RGB image array, uint8 [0-255]
        
    Returns:
        (H, 3) array of mean RGB values per row, normalized to [0, 1]
        
    Raises:
        ValueError: If image shape is not (H, W, 3)
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) RGB image, got shape {image.shape}")
    
    # Mean across width axis, normalize to [0, 1]
    # This is array orchestration (pipeline-level concern)
    mean_per_row = image.mean(axis=1).astype(np.float64) / 255.0
    
    return mean_per_row
