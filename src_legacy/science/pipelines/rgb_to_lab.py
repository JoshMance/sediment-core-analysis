"""Pipeline: Convert RGB to CIELAB color space."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ..functions.srgb_to_linear_rgb import srgb_to_linear_rgb
from ..functions.linear_rgb_to_xyz import linear_rgb_to_xyz
from ..functions.xyz_to_lab import xyz_to_lab
from ..catalog import catalog


def rgb_to_lab(
    rgb: NDArray[np.float64],
    illuminant: str = "D65",
) -> NDArray[np.float64]:
    """Convert RGB values to CIELAB color space.
    
    This pipeline orchestrates three color space transformations:
    1. sRGB → Linear RGB (gamma correction)
    2. Linear RGB → XYZ (color space transformation)
    3. XYZ → LAB (perceptual space transformation)
    
    Args:
        rgb: (..., 3) array of RGB values in [0, 1]
        illuminant: Reference illuminant ('C', 'D50', or 'D65')
        
    Returns:
        (..., 3) array of L*a*b* values
        - L* in [0, 100]
        - a* and b* typically in [-128, 127]
    
    Default uses D65 illuminant and sRGB color space, which is appropriate
    for most digital images.
    """
    # Step 1: sRGB → Linear RGB
    linear = srgb_to_linear_rgb(rgb)
    
    # Step 2: Linear RGB → XYZ
    xyz = linear_rgb_to_xyz(linear)
    
    # Step 3: XYZ → LAB
    white_point = catalog.white_point(illuminant)
    lab = xyz_to_lab(xyz, white_point)
    
    return lab
