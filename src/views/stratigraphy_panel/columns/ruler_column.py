"""Ruler column for displaying depth scale."""

from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QRectF, Qt, QPointF
from .base import BaseColumn
from ..rows import StratRow


class RulerColumn(BaseColumn):
    """
    Column that displays a depth ruler with ticks and labels.
    
    This column consumes the canonical depth scale and renders major/minor
    ticks with depth labels at appropriate intervals.
    """
    
    def __init__(
        self, 
        title: str = "Depth", 
        width: int = 80,
        unit: str = "mm",
        major_tick_length: int = 20,
        minor_tick_length: int = 10
    ) -> None:
        """
        Initialize ruler column.
        
        Args:
            title: Column header title
            width: Relative width weight
            unit: Unit of measurement to display on labels (e.g., "mm", "cm")
            major_tick_length: Length of major tick marks in pixels
            minor_tick_length: Length of minor tick marks in pixels
        """
        super().__init__(title, width)
        self._unit = unit
        self._major_tick_length = major_tick_length
        self._minor_tick_length = minor_tick_length
    
    def provides_scale(self) -> bool:
        """Ruler consumes scale, does not provide it."""
        return False
    
    def get_header_metadata(self) -> dict:
        """Return unit for canvas to render in header."""
        return {'unit': self._unit}
    
    def _calculate_tick_interval(self, depth_span: float) -> tuple[float, float]:
        """
        Calculate appropriate major and minor tick intervals based on depth span.
        
        Args:
            depth_span: Total depth range to display
            
        Returns:
            (major_interval, minor_interval) in depth units
        """
        # Target ~5-10 major ticks
        target_major_ticks = 8
        raw_interval = depth_span / target_major_ticks
        
        # Round to nice values (1, 2, 5, 10, 20, 50, 100, etc.)
        magnitude = 10 ** int(len(str(int(raw_interval))) - 1)
        normalized = raw_interval / magnitude
        
        if normalized <= 1.5:
            major_interval = 1 * magnitude
        elif normalized <= 3:
            major_interval = 2 * magnitude
        elif normalized <= 7:
            major_interval = 5 * magnitude
        else:
            major_interval = 10 * magnitude
        
        # Halve intervals to get twice as many ticks
        major_interval = major_interval / 2
        
        # Minor interval is 1/5 of major
        minor_interval = major_interval / 5
        
        return (major_interval, minor_interval)
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """
        Paint the ruler with ticks and labels.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: (min_depth, max_depth) in depth units
            rows: List of depth intervals (not used by ruler)
        """
        min_depth, max_depth = depth_range
        depth_span = max_depth - min_depth
        
        if depth_span <= 0:
            return
        
        # Calculate tick intervals
        major_interval, minor_interval = self._calculate_tick_interval(depth_span)
        
        # Antialiasing disabled
        # painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Position for right-justified ticks
        ruler_x = rect.x() + rect.width()
        
        # Draw minor ticks
        pen = QPen(QColor(120, 120, 120), 1)
        pen.setCosmetic(True)  # Always 1 physical pixel
        painter.setPen(pen)
        minor_depth = (int(min_depth / minor_interval) + 1) * minor_interval
        
        while minor_depth < max_depth:
            # Skip if this is a major tick position
            is_major = abs(minor_depth % major_interval) < minor_interval * 0.01
            
            if not is_major:
                y = self._depth_to_pixel(minor_depth, rect, depth_range) + 0.5  # Horizontal: y + 0.5
                if rect.top() <= y <= rect.bottom():
                    tick_start = ruler_x - self._minor_tick_length
                    tick_end = ruler_x
                    painter.drawLine(QPointF(tick_start, y), QPointF(tick_end, y))
            
            minor_depth += minor_interval
        
        # Draw major ticks with labels
        pen = QPen(QColor(60, 60, 60), 2)
        pen.setCosmetic(True)  # Always 2 physical pixels
        painter.setPen(pen)
        major_depth = (int(min_depth / major_interval) + 1) * major_interval
        
        while major_depth <= max_depth:
            y = self._depth_to_pixel(major_depth, rect, depth_range) + 0.5  # Horizontal: y + 0.5
            
            if rect.top() <= y <= rect.bottom():
                # Draw major tick (extends left from ruler line)
                tick_start = ruler_x - self._major_tick_length
                tick_end = ruler_x
                painter.drawLine(QPointF(tick_start, y), QPointF(tick_end, y))
                
                # Draw label to the left of the tick
                painter.setPen(QColor(40, 40, 40))
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                
                # Format label (remove trailing zeros and decimal point if whole number)
                label = f"{major_depth:.10g}"
                
                label_rect = QRectF(rect.x(), y - 10, tick_start - rect.x() - 5, 20)
                painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
                
                painter.setPen(QPen(QColor(60, 60, 60), 2))
            
            major_depth += major_interval
