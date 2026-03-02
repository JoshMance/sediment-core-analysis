"""Convert linear RGB to CIE XYZ color space."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


# sRGB to XYZ transformation matrix (D65 illuminant, 2° observer)
# Reference: http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
_SRGB_TO_XYZ_MATRIX = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
], dtype=np.float64)


def linear_rgb_to_xyz(
    linear_rgb: NDArray[np.float64],
    transformation_matrix: NDArray[np.float64] | None = None,
) -> NDArray[np.float64]:
    """Convert linear RGB to CIE XYZ tristimulus values.
    
    Applies a 3x3 transformation matrix to convert from linear RGB
    to device-independent XYZ color space.
    
    Args:
        linear_rgb: (..., 3) array of linear RGB values in [0, 1]
        transformation_matrix: (3, 3) RGB→XYZ matrix. If None, uses sRGB D65 matrix.
        
    Returns:
        (..., 3) array of XYZ tristimulus values
        
    Reference:
        http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    """
    linear_rgb = np.asarray(linear_rgb, dtype=np.float64)
    
    if transformation_matrix is None:
        transformation_matrix = _SRGB_TO_XYZ_MATRIX
    
    # Matrix multiplication: RGB @ M^T -> XYZ
    # Using einsum for arbitrary leading dimensions
    xyz = np.einsum("...c,dc->...d", linear_rgb, transformation_matrix)
    
    return xyz
