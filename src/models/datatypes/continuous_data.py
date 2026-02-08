"""ContinuousData type - numeric values along a position axis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass
class ContinuousData:
    """Continuous numeric data series.
    
    Generic container for numeric values along a position axis.
    Position values default to 0, 1, 2, ... if not specified.
    
    Attributes:
        name: Display name (e.g., "L*", "Red", "Magnetic Susceptibility")
        values: The measurement values
        positions: Position of each value (defaults to 0, 1, 2, ...)
        unit: Unit label (e.g., "%", "SI", "ppm")
        parent: Optional parent reference (for inheriting scale/calibration)
    """
    name: str
    values: NDArray[np.float64]
    positions: NDArray[np.float64] | None = None
    unit: str = ""
    parent: Any | None = None

    def __post_init__(self) -> None:
        """Initialize default positions if not provided."""
        if self.positions is None:
            self.positions = np.arange(len(self.values), dtype=np.float64)

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
    def position_range(self) -> tuple[float, float]:
        """(min, max) position range."""
        return (float(np.min(self.positions)), float(np.max(self.positions)))

    def __len__(self) -> int:
        """Number of data points."""
        return len(self.values)

    def value_at(self, position: float) -> float | None:
        """Get interpolated value at a position (linear interpolation)."""
        if len(self.values) == 0:
            return None
        return float(np.interp(position, self.positions, self.values))
