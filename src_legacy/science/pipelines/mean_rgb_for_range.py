"""Pipeline: Compute mean RGB for a range of rows."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def mean_rgb_for_range(
    rgb_per_row: NDArray[np.float64],
    start_row: int,
    end_row: int,
) -> NDArray[np.float64]:
    """Compute mean RGB for a range of rows.
    
    This is a pipeline that handles array slicing and aggregation logic.
    
    Args:
        rgb_per_row: (H, 3) array from mean_rgb_per_row pipeline
        start_row: Start row index (inclusive)
        end_row: End row index (exclusive)
        
    Returns:
        (3,) array with mean [R, G, B] values in [0, 1]
        If range is invalid, returns mid-gray [0.5, 0.5, 0.5]
    """
    # Validate range
    if start_row >= end_row or start_row < 0 or end_row > len(rgb_per_row):
        # Return mid-gray for invalid ranges
        return np.array([0.5, 0.5, 0.5], dtype=np.float64)
    
    # Slice and aggregate (array orchestration - pipeline-level concern)
    mean = rgb_per_row[start_row:end_row].mean(axis=0)
    
    return mean
