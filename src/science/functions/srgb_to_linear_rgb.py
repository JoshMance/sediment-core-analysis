"""Convert sRGB to linear RGB (gamma correction)."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def srgb_to_linear_rgb(srgb: NDArray[np.float64]) -> NDArray[np.float64]:
    """Apply inverse gamma correction to convert sRGB to linear RGB.
    
    This is the first step in converting sRGB color values to other color spaces.
    sRGB uses a gamma curve to approximate human perception; we linearize it
    to perform colorimetric calculations.
    
    Args:
        srgb: (..., 3) array of sRGB values in [0, 1]
        
    Returns:
        (..., 3) array of linear RGB values in [0, 1]
        
    Reference:
        IEC 61966-2-1:1999 (sRGB standard)
        https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ
    """
    srgb = np.asarray(srgb, dtype=np.float64)
    
    # Inverse sRGB companding (gamma correction)
    # For values <= 0.04045: linear scaling
    # For values > 0.04045: power function
    linear = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4
    )
    
    return linear
