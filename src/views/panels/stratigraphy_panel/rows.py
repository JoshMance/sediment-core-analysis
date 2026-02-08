"""
Row definitions for stratigraphy panel.

Rows represent depth intervals between dividers and are managed by the canvas.
"""

from dataclasses import dataclass


@dataclass
class StratRow:
    """
    Value object representing a depth interval between two dividers.
    
    Canvas owns and manages these. Columns receive them as read-only
    rendering hints.
    """
    id: str
    min_depth: float
    max_depth: float
    
    @property
    def depth_span(self) -> float:
        """Get the depth span of this row."""
        return self.max_depth - self.min_depth
