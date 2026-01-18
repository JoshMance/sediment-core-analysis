from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QRectF, Qt, QPointF
from .column import Column

class DataColumn(Column):
    """Column that displays numerical data as a line graph."""
    
    def __init__(self, title: str, data: list[float] | None = None, 
                 min_value: float = 0.0, max_value: float = 1.0, width: int = 100,
                 color: QColor = None) -> None:
        super().__init__(title, width)
        self.data = data or []
        self.min_value = min_value
        self.max_value = max_value
        self.color = color or QColor(Qt.black)
    
    def set_data(self, data: list[float], min_value: float = None, max_value: float = None) -> None:
        """Set the data to display."""
        self.data = data
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Content height matches the number of data points (1 pixel per data point)."""
        return float(len(self.data))
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float]) -> None:
        """Paint the data as a line graph."""
        if not self.data or len(self.data) == 0:
            return
        
        # Enable antialiasing for smooth lines
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Normalize data to column width
        data_range = self.max_value - self.min_value
        if data_range == 0:
            data_range = 1.0
        
        # Draw line graph
        painter.setPen(QPen(self.color, 1))
        
        points = []
        for i, value in enumerate(self.data):
            # Normalize value to 0-1 range
            normalized = (value - self.min_value) / data_range
            normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1
            
            # Map to pixel position
            x = rect.x() + (normalized * rect.width())
            y = rect.y() + i  # 1 pixel per data point vertically
            
            points.append(QPointF(x, y))
        
        # Draw connected line
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        
        painter.setRenderHint(QPainter.Antialiasing, False)
