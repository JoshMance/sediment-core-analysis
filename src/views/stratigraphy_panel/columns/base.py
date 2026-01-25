"""
Base column class with common functionality.
"""

from PySide6.QtGui import QPainter, QPen
from PySide6.QtCore import QRectF, Qt
from ..rows import StratRow


# Layout constants
HEADER_HEIGHT = 55
TITLE_HEIGHT = 50
DOMAIN_PADDING = 10  # Inner padding for data columns


class BaseColumn:
    """
    Thin base class providing common column behavior.
    
    Handles:
    - Header rendering (title display)
    - Scroll offset management
    - Content clipping
    
    Subclasses must override _paint_content() to render their specific data.
    """
    
    def __init__(self, title: str, width: int = 100) -> None:
        """
        Initialize base column.
        
        Args:
            title: Column header title
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
    
    def paint(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], scroll_offset: float = 0.0, rows: list[StratRow] = None) -> None:
        """
        Paint this column.
        
        Args:
            painter: QPainter to draw with
            rect: The rectangular area allocated for this column
            depth_range: (min_depth, max_depth) in depth units
            scroll_offset: Vertical scroll offset in pixels
            rows: Optional list of depth intervals (for dividers/regions)
        """
        if rows is None:
            rows = []
        
        # Paint header (always fixed at top)
        self._paint_header(painter, rect)
        
        # Antialiasing disabled
        # painter.setRenderHint(QPainter.Antialiasing)
        
        # Paint content area (below header, with scrolling)
        content_rect = QRectF(rect.x(), rect.y() + HEADER_HEIGHT, rect.width(), rect.height() - HEADER_HEIGHT)
        
        # Save painter state and set clipping to content area
        painter.save()
        painter.setClipRect(content_rect)
        
        # Adjust content rect for scroll offset
        scrolled_content_rect = content_rect.translated(0, -scroll_offset)
        self._paint_content(painter, scrolled_content_rect, depth_range, rows)
        
        painter.restore()
    
    def _paint_header(self, painter: QPainter, rect: QRectF) -> None:
        """Paint the column header with title."""
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), HEADER_HEIGHT)
        
        # Draw header background
        painter.fillRect(header_rect, Qt.white)
        
        # Draw header borders (top, bottom, left only - right is drawn by next column)
        painter.setPen(QPen(Qt.black, 1))
        # Top border
        painter.drawLine(header_rect.topLeft(), header_rect.topRight())
        # Bottom border
        painter.drawLine(header_rect.bottomLeft(), header_rect.bottomRight())
        # Left border
        painter.drawLine(header_rect.topLeft(), header_rect.bottomLeft())
        
        # Draw title text
        painter.drawText(header_rect, Qt.AlignCenter, self.title)
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """
        Paint the column content area.
        
        Override in subclasses to render specific data.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
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
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains data."""
        return False
