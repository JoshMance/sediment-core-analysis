from PySide6.QtGui import QPainter, QPen
from PySide6.QtCore import QRectF, Qt

# Column header height
HEADER_HEIGHT = 40
TITLE_HEIGHT = 50

class Column:
    """Base class for stratigraphy columns."""
    
    def __init__(self, title: str, width: int = 100) -> None:
        self.title = title
        self.width = width
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Calculate the total content height needed (for scrolling)."""
        return 0.0  # Override in subclasses
    
    def paint(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], scroll_offset: float = 0.0) -> None:
        """
        Paint this column.
        
        Args:
            painter: QPainter to draw with
            rect: The rectangular area allocated for this column
            depth_range: (min_depth, max_depth) in depth units
            scroll_offset: Vertical scroll offset in pixels
        """
        # Paint header (always fixed at top)
        self._paint_header(painter, rect)
        
        # Paint content area (below header, with scrolling)
        content_rect = QRectF(rect.x(), rect.y() + HEADER_HEIGHT, rect.width(), rect.height() - HEADER_HEIGHT)
        
        # Save painter state and set clipping to content area
        painter.save()
        painter.setClipRect(content_rect)
        
        # Adjust content rect for scroll offset
        scrolled_content_rect = content_rect.translated(0, -scroll_offset)
        self._paint_content(painter, scrolled_content_rect, depth_range)
        
        painter.restore()
    
    def _paint_header(self, painter: QPainter, rect: QRectF) -> None:
        """Paint the column header with title."""
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), HEADER_HEIGHT)
        
        # Draw header background
        painter.fillRect(header_rect, Qt.white)
        
        # Draw header border
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(header_rect)
        
        # Draw title text
        painter.drawText(header_rect, Qt.AlignCenter, self.title)
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float]) -> None:
        """Paint the column content area (override in subclasses)."""
        # Default: nothing (subclasses override)
        pass
