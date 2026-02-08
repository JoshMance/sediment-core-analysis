"""CategoricalData type - discrete labels at boundary-defined intervals."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass
class CategoricalData:
    """Categorical data with labels for intervals defined by boundaries.
    
    Generic container for discrete labels that apply to intervals.
    N boundaries define N-1 intervals, each with a label.
    
    Attributes:
        name: Display name (e.g., "Lithology", "Munsell")
        labels: Category labels for each interval (len = len(boundaries) - 1)
        boundaries: Position values where categories change
        parent: Optional parent reference (for sharing boundary definitions)
    """
    name: str
    labels: list[str] = field(default_factory=list)
    boundaries: NDArray[np.float64] = field(default_factory=lambda: np.array([], dtype=np.float64))
    parent: Any | None = None

    def __post_init__(self) -> None:
        """Validate labels/boundaries relationship."""
        self._validate()

    def _validate(self) -> None:
        """Ensure labels count matches boundary intervals."""
        if len(self.boundaries) > 0 and len(self.labels) != len(self.boundaries) - 1:
            raise ValueError(
                f"labels count ({len(self.labels)}) must be boundaries count - 1 "
                f"({len(self.boundaries) - 1})"
            )

    @property
    def interval_count(self) -> int:
        """Number of intervals (len(boundaries) - 1)."""
        return max(0, len(self.boundaries) - 1)

    def get_interval(self, index: int) -> tuple[float, float, str] | None:
        """Get (start, end, label) for an interval by index."""
        if 0 <= index < self.interval_count:
            return (
                float(self.boundaries[index]),
                float(self.boundaries[index + 1]),
                self.labels[index]
            )
        return None

    def label_at(self, position: float) -> str | None:
        """Get the label at a given position."""
        for i in range(self.interval_count):
            start = self.boundaries[i]
            end = self.boundaries[i + 1]
            if start <= position < end:
                return self.labels[i]
        return None

    def set_label(self, index: int, label: str) -> None:
        """Set label for a specific interval."""
        if 0 <= index < len(self.labels):
            self.labels[index] = label

    def add_boundary(self, position: float, label_before: str = "", label_after: str = "") -> None:
        """Insert a new boundary, splitting an existing interval.
        
        Args:
            position: Where to insert the new boundary
            label_before: Label for the interval before the new boundary
            label_after: Label for the interval after the new boundary
        """
        # Find insertion point
        insert_idx = np.searchsorted(self.boundaries, position)
        
        # Insert boundary
        self.boundaries = np.insert(self.boundaries, insert_idx, position)
        
        # Handle labels
        if len(self.labels) == 0:
            # First split: need both labels
            if insert_idx == 0:
                self.labels = [label_after]
            else:
                self.labels = [label_before]
        else:
            # Existing intervals: split the current one
            if insert_idx > 0 and insert_idx <= len(self.labels):
                # We're splitting an existing interval
                old_label = self.labels[insert_idx - 1]
                self.labels[insert_idx - 1] = label_before or old_label
                self.labels.insert(insert_idx, label_after or old_label)
            else:
                # Edge case: inserting at start or end
                self.labels.insert(insert_idx, label_after or label_before)
