"""
Unified column definitions for stratigraphy panel.

Uses polymorphism with a thin base class to define common behavior.
Each concrete column class owns and validates its own data format.
"""

from typing import Protocol, runtime_checkable
from PySide6.QtGui import QPainter, QPen, QPixmap, QColor, QTransform
from PySide6.QtCore import QRectF, Qt, QPointF


# Constants
HEADER_HEIGHT = 40
TITLE_HEIGHT = 50


@runtime_checkable
class ColumnProtocol(Protocol):
    """
    Protocol defining the interface for stratigraphy columns.
    
    All columns must implement these methods to work with the canvas.
    """
    
    title: str
    width: int
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Calculate the total content height needed (for scrolling)."""
        ...
    
    def paint(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], scroll_offset: float) -> None:
        """Paint this column in the given rect."""
        ...
    
    @property
    def supports_interaction(self) -> bool:
        """Whether this column supports user interaction."""
        ...
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains data."""
        ...


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
        """
        Paint the column content area.
        
        Override in subclasses to render specific data.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: (min_depth, max_depth) in depth units
        """
        pass
    
    @property
    def supports_interaction(self) -> bool:
        """Whether this column supports user interaction."""
        return False
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains data."""
        return False


class ImageColumn(BaseColumn):
    """
    Column that displays an image (e.g., sediment core photo).
    
    Owns and manages:
    - QPixmap data
    - Automatic orientation correction (rotates if width > height)
    - Aspect ratio preservation
    """
    
    def __init__(self, title: str, pixmap: QPixmap | None = None, width: int = 200) -> None:
        """
        Initialize image column.
        
        Args:
            title: Column header title
            pixmap: Image to display (will be auto-rotated if needed)
            width: Relative width weight
        """
        super().__init__(title, width)
        self._pixmap: QPixmap | None = None
        if pixmap:
            self.set_pixmap(pixmap)
    
    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Set the image to display.
        
        Automatically ensures vertical orientation by rotating if needed.
        
        Args:
            pixmap: Image to display
        """
        self._pixmap = self._ensure_vertical_orientation(pixmap)
    
    def get_pixmap(self) -> QPixmap | None:
        """Get the current pixmap."""
        return self._pixmap
    
    def _ensure_vertical_orientation(self, pixmap: QPixmap) -> QPixmap:
        """
        Rotate image 90° if width > height to make longest side vertical.
        
        Args:
            pixmap: Input image
            
        Returns:
            Oriented image (original or rotated)
        """
        if not pixmap or pixmap.isNull():
            return pixmap
        
        # If width > height, rotate 90 degrees
        if pixmap.width() > pixmap.height():
            transform = QTransform()
            transform.rotate(90)
            return pixmap.transformed(transform, Qt.SmoothTransformation)
        
        return pixmap
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """
        Calculate the height needed to display image at correct aspect ratio.
        
        Args:
            width: Actual pixel width allocated to this column
            depth_range: Not used for images
            
        Returns:
            Height in pixels to maintain aspect ratio
        """
        if not self._pixmap or self._pixmap.isNull():
            return 0.0
        
        # Calculate height needed to maintain aspect ratio at given width
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        return width * aspect_ratio
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float]) -> None:
        """
        Paint the image maintaining aspect ratio.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: Not used for images
        """
        if not self._pixmap or self._pixmap.isNull():
            return
        
        # Scale to column width, maintain aspect ratio
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        scaled_height = rect.width() * aspect_ratio
        
        # Create rect for scaled image starting at top of content area
        image_rect = QRectF(rect.x(), rect.y(), rect.width(), scaled_height)
        
        # Draw the image
        painter.drawPixmap(image_rect.toRect(), self._pixmap)
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains valid image data."""
        return self._pixmap is not None and not self._pixmap.isNull()


class DataColumn(BaseColumn):
    """
    Column that displays numerical data as a line graph.
    
    Owns and manages:
    - List of float values (one per depth increment)
    - Min/max value range for normalization
    - Line color
    - Graph rendering
    """
    
    def __init__(
        self, 
        title: str, 
        data: list[float] | None = None,
        min_value: float = 0.0, 
        max_value: float = 1.0, 
        width: int = 100,
        color: QColor | None = None
    ) -> None:
        """
        Initialize data column.
        
        Args:
            title: Column header title
            data: List of numerical values to plot
            min_value: Minimum value for normalization (left edge of graph)
            max_value: Maximum value for normalization (right edge of graph)
            width: Relative width weight
            color: Line color (defaults to black)
        """
        super().__init__(title, width)
        self._data: list[float] = data or []
        self._min_value = min_value
        self._max_value = max_value
        self._color = color or QColor(Qt.black)
        self._validate_data()
    
    def set_data(self, data: list[float], min_value: float | None = None, max_value: float | None = None) -> None:
        """
        Set the data to display.
        
        Args:
            data: List of numerical values to plot
            min_value: Optional new minimum value for normalization
            max_value: Optional new maximum value for normalization
        """
        self._data = data
        if min_value is not None:
            self._min_value = min_value
        if max_value is not None:
            self._max_value = max_value
        self._validate_data()
    
    def get_data(self) -> list[float]:
        """Get the current data."""
        return self._data.copy()
    
    def set_color(self, color: QColor) -> None:
        """Set the line color."""
        self._color = color
    
    def get_color(self) -> QColor:
        """Get the current line color."""
        return self._color
    
    def _validate_data(self) -> None:
        """Validate data and range."""
        if self._max_value <= self._min_value:
            raise ValueError(f"max_value ({self._max_value}) must be greater than min_value ({self._min_value})")
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """
        Content height matches the number of data points (1 pixel per data point).
        
        Args:
            width: Not used for data columns
            depth_range: Not used for data columns
            
        Returns:
            Height in pixels (one per data point)
        """
        return float(len(self._data))
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float]) -> None:
        """
        Paint the data as a line graph.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: Not used for data columns
        """
        if not self._data or len(self._data) == 0:
            return
        
        # Enable antialiasing for smooth lines
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Normalize data to column width
        data_range = self._max_value - self._min_value
        
        # Draw line graph
        painter.setPen(QPen(self._color, 1))
        
        points = []
        for i, value in enumerate(self._data):
            # Normalize value to 0-1 range
            normalized = (value - self._min_value) / data_range
            normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
            
            # Map to pixel position
            x = rect.x() + (normalized * rect.width())
            y = rect.y() + i  # 1 pixel per data point vertically
            
            points.append(QPointF(x, y))
        
        # Draw connected line
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        
        painter.setRenderHint(QPainter.Antialiasing, False)
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains data."""
        return len(self._data) > 0
