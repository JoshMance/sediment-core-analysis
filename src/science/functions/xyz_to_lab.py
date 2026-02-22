"""Convert CIE XYZ to CIELAB color space."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def xyz_to_lab(
    xyz: NDArray[np.float64],
    white_point: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Convert CIE XYZ tristimulus values to CIELAB color space.
    
    CIELAB is a perceptually uniform color space designed to approximate
    human vision. L* represents lightness, a* and b* represent color opponents.
    
    Args:
        xyz: (..., 3) array of XYZ tristimulus values
        white_point: (3,) array of reference white point XYZ values
                     (e.g., D65: [0.95047, 1.0, 1.08883])
        
    Returns:
        (..., 3) array of L*a*b* values
        - L* in [0, 100] (lightness: 0=black, 100=white)
        - a* typically in [-128, 127] (green-red opponent)
        - b* typically in [-128, 127] (blue-yellow opponent)
        
    Reference:
        http://www.brucelindbloom.com/index.html?Eqn_XYZ_to_Lab.html
        CIE 15:2004 "Colorimetry"
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    white_point = np.asarray(white_point, dtype=np.float64)
    
    # Normalize by white point
    xyz_normalized = xyz / white_point
    
    # f(t) function for Lab conversion
    # Piecewise function with threshold at (6/29)^3
    delta = 6.0 / 29.0
    threshold = delta ** 3
    
    f = np.where(
        xyz_normalized > threshold,
        xyz_normalized ** (1.0 / 3.0),
        xyz_normalized / (3.0 * delta ** 2) + 4.0 / 29.0
    )
    
    # Extract f(X/Xn), f(Y/Yn), f(Z/Zn)
    fx = f[..., 0]
    fy = f[..., 1]
    fz = f[..., 2]
    
    # Calculate L*, a*, b*
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    
    return np.stack([L, a, b], axis=-1)
