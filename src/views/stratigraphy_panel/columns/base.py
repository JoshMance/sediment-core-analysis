"""
Base column class with common functionality.
"""

from PySide6.QtGui import QPainter
from PySide6.QtCore import QRectF
from ..rows import StratRow


# Layout constants
HEADER_HEIGHT = 55
TITLE_HEIGHT = 50
DOMAIN_PADDING = 10  # Inner padding for data columns


class BaseColumn:
    """
    Base class for columns - only renders data content.
    
    Canvas handles all structural elements (headers, borders, titles).
    Columns focus solely on rendering their specific data.
    """
    
    def __init__(self, title: str, width: int = 100) -> None:
        """
        Initialize base column.
        
        Args:
            title: Column title (rendered by canvas in header)
            width: Relative width weight (used for proportional sizing)
        """
        self.title = title
        self.width = width
    
    def provides_scale(self) -> bool:
        """Whether this column defines the canonical depth scale."""
        return False
    
    def get_scale(self, width: float) -> tuple[float, tuple[float, float]] | None:
        """
        Get the scale this column defines.
        
        Override in subclasses that provide scale (e.g., ImageColumn).
        
        Args:
            width: Actual pixel width allocated to this column
            
        Returns:
            (pixel_height, (min_depth, max_depth)) if provides_scale, else None
        """
        return None
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """
        Calculate the total content height needed (for scrolling).
        
        Override in subclasses to return the actual content height.
        
        Args:
            width: Actual pixel width allocated to this column
            depth_range: (min_depth, max_depth) in depth units
            
        Returns:
            Height in pixels
        """
        return 0.0
    
    def get_header_metadata(self) -> dict:
        """
        Get metadata for canvas to render in header.
        
        Override in subclasses to provide custom header elements.
        
        Returns:
            Dict with optional keys: 'domain_range', 'unit', etc.
        """
        return {}
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """
        Paint only the column data content.
        
        Canvas handles headers and borders. This method should only draw
        the actual data (graphs, images, rulers, etc.).
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already clipped and scroll-adjusted)
            depth_range: (min_depth, max_depth) in depth units
            rows: List of depth intervals for dividers/regions
        """
        pass
    
    def _depth_to_pixel(self, depth: float, rect: QRectF, depth_range: tuple[float, float]) -> float:
        """
        Convert depth value to pixel Y coordinate within rect.
        
        Args:
            depth: Depth value to convert
            rect: Rectangle containing the content
            depth_range: (min_depth, max_depth) full range
            
        Returns:
            Y pixel coordinate
        """
        if depth_range[1] == depth_range[0]:
            return rect.top()
        
        normalized = (depth - depth_range[0]) / (depth_range[1] - depth_range[0])
        return rect.top() + (normalized * rect.height())
