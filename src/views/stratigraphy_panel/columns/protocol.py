"""
Column protocol defining the interface for stratigraphy columns.
"""

from typing import Protocol, runtime_checkable
from PySide6.QtGui import QPainter
from PySide6.QtCore import QRectF
from ..rows import StratRow


@runtime_checkable
class ColumnProtocol(Protocol):
    """
    Protocol defining the interface for stratigraphy columns.
    
    All columns must implement these methods to work with the canvas.
    """
    
    title: str
    width: int
    
    def provides_scale(self) -> bool:
        """Whether this column defines the canonical depth scale."""
        ...
    
    def get_scale(self, width: float) -> tuple[float, tuple[float, float]] | None:
        """
        Get the scale this column defines.
        
        Returns:
            (pixel_height, (min_depth, max_depth)) if provides_scale, else None
        """
        ...
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Calculate the total content height needed (for scrolling)."""
        ...
    
    def paint(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], scroll_offset: float, rows: list['StratRow']) -> None:
        """Paint this column in the given rect."""
        ...
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains data."""
        ...
