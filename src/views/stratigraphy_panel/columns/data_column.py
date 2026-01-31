"""Data column for displaying line graph data."""

from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QRectF, Qt, QPointF
from .base import BaseColumn, HEADER_HEIGHT, DOMAIN_PADDING
from ..rows import StratRow


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
        Return arbitrary height - actual scaling happens in paint.
        
        Data points will be mapped to physical depths and rendered at whatever
        scale the canvas provides via rect height.
        
        Args:
            width: Not used for data columns
            depth_range: Not used for height calculation
            
        Returns:
            Nominal height (actual layout determined by canvas scale)
        """
        return float(len(self._data)) if self._data else 0.0
    
    def get_header_metadata(self) -> dict:
        """Return domain range for canvas to render in header."""
        return {
            'domain_range': (self._min_value, self._max_value),
            'color': self._color
        }
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """
        Paint the data as a line graph with optional row dividers.
        
        Maps data points to rect height proportionally so all columns align to the same scale.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: Depth range for positioning
            rows: List of depth intervals (can draw dividers or highlights)
        """
        if not self._data or len(self._data) == 0:
            return
        
        # Antialiasing disabled
        # painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Apply inner padding to create data domain
        domain_rect = rect.adjusted(DOMAIN_PADDING, 0, -DOMAIN_PADDING, 0)
        
        # Draw vertical guide lines at min, mid, and max positions
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # Min line (left edge)
        min_x = domain_rect.x()
        painter.drawLine(QPointF(min_x, domain_rect.top()), QPointF(min_x, domain_rect.bottom()))
        
        # Mid line (center)
        mid_x = domain_rect.x() + domain_rect.width() / 2
        painter.drawLine(QPointF(mid_x, domain_rect.top()), QPointF(mid_x, domain_rect.bottom()))
        
        # Max line (right edge)
        max_x = domain_rect.x() + domain_rect.width()
        painter.drawLine(QPointF(max_x, domain_rect.top()), QPointF(max_x, domain_rect.bottom()))
        
        # Normalize data to domain width (horizontal)
        data_range = self._max_value - self._min_value
        
        # Draw line graph
        painter.setPen(QPen(self._color, 1))
        
        # Map data points to rect height proportionally
        # This ensures data aligns with image at the same vertical positions
        num_points = len(self._data)
        height_per_point = domain_rect.height() / num_points if num_points > 1 else domain_rect.height()
        
        points = []
        for i, value in enumerate(self._data):
            # Normalize value to 0-1 range (horizontal position)
            normalized = (value - self._min_value) / data_range
            normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
            
            # Map to pixel position within padded domain
            x = domain_rect.x() + (normalized * domain_rect.width())
            y = domain_rect.y() + (i * height_per_point)  # Proportional to rect height
            
            points.append(QPointF(x, y))
        
        # Draw connected line
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
