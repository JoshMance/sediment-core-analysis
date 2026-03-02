"""Data type - measurements along a single axis with vector-valued points.

This datatype represents measurements along ONE axis (dimension) such as depth
down a core. Each point along that axis can be:
- Scalar-valued: a single number (e.g., magnetic susceptibility)
- Vector-valued: multiple components (e.g., RGB as [R, G, B], or CIELAB as [L*, a*, b*])

Shapes:
- Scalar data: values shape (H,) - H points, each is a single number
- Vector data: values shape (H, N) - H points, each is an N-component vector
  Example: RGB per row is (H, 3) - H depth points, each is [R, G, B]

This is NOT multi-dimensional in the sense of having multiple independent axes.
We have ONE axis (depth/position) with measurements at each point.

Stores:
- values: array of measurements, shape (H,) for scalars or (H, N) for N-component vectors
- axis: coordinate positions along the single axis (e.g. pixel rows, depth in mm)

If no axis is provided, the series is indexed [0..n-1].
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class Data:
    """Numeric data series: measurements along a single axis.
    
    Represents measurements along ONE axis (e.g., depth down a core),
    where each point can be scalar or vector-valued.
    
    Examples:
    - Scalar: Magnetic susceptibility at each depth → shape (H,)
    - Vector: RGB color at each depth → shape (H, 3) where each point is [R, G, B]
    - Vector: CIELAB at each depth → shape (H, 3) where each point is [L*, a*, b*]
    
    This is NOT a 2D matrix with two independent axes. It's ONE axis (depth)
    with potentially multi-component measurements at each point.
    
    Attributes:
        name: Display name (e.g., "RGB", "L*a*b*", "Magnetic Susceptibility")
        values: Measurement values, shape (H,) for scalars or (H, N) for N-component vectors
        axis: Coordinate of each measurement point (defaults to 0, 1, 2, ...)
        unit: Unit label (e.g., "%", "SI", "ppm")
    """
    name: str
    values: NDArray[np.float64]
    axis: NDArray[np.float64] | None = None
    unit: str = ""

    def __post_init__(self) -> None:
        """Initialize default axis if not provided."""
        if self.axis is None:
            self.axis = np.arange(len(self.values), dtype=np.float64)

    @property
    def min_value(self) -> float:
        """Minimum value in the series."""
        return float(np.min(self.values))

    @property
    def max_value(self) -> float:
        """Maximum value in the series."""
        return float(np.max(self.values))

    @property
    def value_range(self) -> tuple[float, float]:
        """(min, max) value range."""
        return (self.min_value, self.max_value)

    @property
    def axis_range(self) -> tuple[float, float]:
        """(min, max) axis range."""
        return (float(np.min(self.axis)), float(np.max(self.axis)))

    def __len__(self) -> int:
        """Number of data points."""
        return len(self.values)

    def value_at(self, position: float) -> float | None:
        """Get interpolated value at an axis position (linear interpolation)."""
        if len(self.values) == 0:
            return None
        return float(np.interp(position, self.axis, self.values))
