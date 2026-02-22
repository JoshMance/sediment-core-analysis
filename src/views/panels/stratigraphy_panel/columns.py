"""
Column definitions for stratigraphy panel.

All column types consolidated into a single file:
- BaseColumn: Abstract base with common functionality
- ImageColumn: Displays sediment core photos
- RulerColumn: Depth scale with ticks/labels
- DataColumn: Line graph for continuous data
- LayerColumn: Discrete stratigraphic intervals
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple, Callable

from PySide6.QtGui import QPainter, QPixmap, QTransform, QPen, QColor, QBrush
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtSvg import QSvgRenderer

if TYPE_CHECKING:
    from models import Layer, ImageCalibration


# =============================================================================
# Layout Constants
# =============================================================================

HEADER_HEIGHT = 55
TITLE_HEIGHT = 50
HEADER_GAP = 5  # Gap between header and content area
DOMAIN_PADDING = 10  # Inner padding for data columns


# =============================================================================
# StratRow - View-local rendering hint
# =============================================================================

class StratRow(NamedTuple):
    """
    View-local rendering hint representing a depth interval.
    
    This is NOT a domain object - it's computed from Layer entities
    for rendering purposes. The authoritative layer state lives in
    CoreAnalysis.layers.
    """
    id: str
    min_depth: float  # in mm (display units)
    max_depth: float  # in mm (display units)
    layer_index: int  # index into CoreAnalysis.layers
    
    @property
    def depth_span(self) -> float:
        """Get the depth span of this row."""
        return self.max_depth - self.min_depth


def rows_from_layers(layers: list[Layer], core) -> list[StratRow]:
    """
    Convert entity layers to view-local StratRows.
    
    Args:
        layers: List of Layer entities from CoreAnalysis
        core: Core entity for pixel-to-depth conversion
        
    Returns:
        List of StratRow rendering hints
    """
    rows = []
    for i, layer in enumerate(layers):
        min_depth = core.px_to_depth(layer.start_px)
        max_depth = core.px_to_depth(layer.end_px)
        rows.append(StratRow(
            id=f"layer_{i}",
            min_depth=min_depth,
            max_depth=max_depth,
            layer_index=i,
        ))
    return rows


# =============================================================================
# BaseColumn
# =============================================================================

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


# =============================================================================
# ImageColumn
# =============================================================================

class ImageColumn(BaseColumn):
    """
    Column that displays an image (e.g., sediment core photo).
    
    Owns and manages:
    - QPixmap data
    - Automatic orientation correction (rotates if width > height)
    - Aspect ratio preservation
    - Canonical depth scale (pixel height maps to physical depth range)
    """
    
    def __init__(
        self, 
        title: str, 
        pixmap: QPixmap | None = None, 
        width: int = 200,
        depth_range: tuple[float, float] | None = None,
        defines_scale: bool = True
    ) -> None:
        """
        Initialize image column.
        
        Args:
            title: Column header title
            pixmap: Image to display (will be auto-rotated if needed)
            width: Relative width weight
            depth_range: Physical depth range this image represents (min, max)
            defines_scale: Whether this column defines the canonical depth scale
        """
        super().__init__(title, width)
        self._pixmap: QPixmap | None = None
        self._depth_range = depth_range
        self._defines_scale = defines_scale
        if pixmap:
            self.set_pixmap(pixmap)
    
    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Set the image to display.
        
        Automatically ensures vertical orientation by rotating if needed.
        """
        self._pixmap = self._ensure_vertical_orientation(pixmap)
    
    def get_pixmap(self) -> QPixmap | None:
        """Get the current pixmap."""
        return self._pixmap
    
    def set_depth_range(self, min_depth: float, max_depth: float) -> None:
        """Set the physical depth range this image represents."""
        self._depth_range = (min_depth, max_depth)
    
    def set_calibration(self, mm_per_pixel: float, offset_mm: float = 0.0) -> None:
        """
        Set scale factor from image pixels to real-world depth.
        
        Args:
            mm_per_pixel: Physical depth per image pixel
            offset_mm: Starting depth in mm (default 0.0)
        """
        if not self._pixmap:
            return
        
        image_height_px = self._pixmap.height()
        total_depth_mm = image_height_px * mm_per_pixel
        self.set_depth_range(offset_mm, offset_mm + total_depth_mm)
    
    def provides_scale(self) -> bool:
        """This column defines scale if it has both image and depth range."""
        return self._defines_scale and self._pixmap is not None and self._depth_range is not None
    
    def get_scale(self, width: float) -> tuple[float, tuple[float, float]] | None:
        """Get the canonical scale: pixel height and physical depth range."""
        if not self.provides_scale():
            return None
        
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        pixel_height = width * aspect_ratio
        
        return (pixel_height, self._depth_range)
    
    def _ensure_vertical_orientation(self, pixmap: QPixmap) -> QPixmap:
        """Rotate image 90° if width > height to make longest side vertical."""
        if not pixmap or pixmap.isNull():
            return pixmap
        
        if pixmap.width() > pixmap.height():
            transform = QTransform()
            transform.rotate(90)
            return pixmap.transformed(transform, Qt.SmoothTransformation)
        
        return pixmap
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Calculate height based on aspect ratio."""
        if not self._pixmap or self._pixmap.isNull():
            return 0.0
        
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        natural_height = width * aspect_ratio
        
        if self.provides_scale():
            return natural_height
        
        if self._depth_range and depth_range:
            our_depth_span = self._depth_range[1] - self._depth_range[0]
            external_depth_span = depth_range[1] - depth_range[0]
            if external_depth_span > 0:
                scale_factor = our_depth_span / external_depth_span
                return natural_height * scale_factor
        
        return natural_height
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """Paint the image maintaining aspect ratio."""
        if not self._pixmap or self._pixmap.isNull():
            return
        
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        scaled_height = rect.width() * aspect_ratio
        
        image_rect = QRectF(rect.x(), rect.y(), rect.width(), scaled_height)
        painter.drawPixmap(image_rect.toRect(), self._pixmap)


# =============================================================================
# RulerColumn
# =============================================================================

class RulerColumn(BaseColumn):
    """
    Column that displays a depth ruler with ticks and labels.
    
    Consumes the canonical depth scale and renders major/minor
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
            unit: Unit of measurement to display on labels
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
        """Calculate appropriate major and minor tick intervals."""
        target_major_ticks = 8
        raw_interval = depth_span / target_major_ticks
        
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
        
        major_interval = major_interval / 2
        minor_interval = major_interval / 5
        
        return (major_interval, minor_interval)
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """Paint the ruler with ticks and labels."""
        min_depth, max_depth = depth_range
        depth_span = max_depth - min_depth
        
        if depth_span <= 0:
            return
        
        major_interval, minor_interval = self._calculate_tick_interval(depth_span)
        ruler_x = rect.x() + rect.width()
        
        # Draw minor ticks
        pen = QPen(QColor(120, 120, 120), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        minor_depth = (int(min_depth / minor_interval) + 1) * minor_interval
        
        while minor_depth < max_depth:
            is_major = abs(minor_depth % major_interval) < minor_interval * 0.01
            
            if not is_major:
                y = self._depth_to_pixel(minor_depth, rect, depth_range) + 0.5
                if rect.top() <= y <= rect.bottom():
                    tick_start = ruler_x - self._minor_tick_length
                    tick_end = ruler_x
                    painter.drawLine(QPointF(tick_start, y), QPointF(tick_end, y))
            
            minor_depth += minor_interval
        
        # Draw major ticks with labels
        pen = QPen(QColor(60, 60, 60), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        major_depth = (int(min_depth / major_interval) + 1) * major_interval
        
        while major_depth <= max_depth:
            y = self._depth_to_pixel(major_depth, rect, depth_range) + 0.5
            
            if rect.top() <= y <= rect.bottom():
                tick_start = ruler_x - self._major_tick_length
                tick_end = ruler_x
                painter.drawLine(QPointF(tick_start, y), QPointF(tick_end, y))
                
                painter.setPen(QColor(40, 40, 40))
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                
                label = f"{major_depth:.10g}"
                label_rect = QRectF(rect.x(), y - 10, tick_start - rect.x() - 5, 20)
                painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
                
                painter.setPen(QPen(QColor(60, 60, 60), 2))
            
            major_depth += major_interval


# =============================================================================
# DataColumn
# =============================================================================

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
        """Set the data to display."""
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
        """Return arbitrary height - actual scaling happens in paint."""
        return float(len(self._data)) if self._data else 0.0
    
    def get_header_metadata(self) -> dict:
        """Return domain range for canvas to render in header."""
        return {
            'domain_range': (self._min_value, self._max_value),
            'color': self._color
        }
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """Paint the data as a line graph."""
        if not self._data or len(self._data) == 0:
            return
        
        domain_rect = rect.adjusted(DOMAIN_PADDING, 0, -DOMAIN_PADDING, 0)
        
        # Draw vertical guide lines at min, mid, and max positions
        pen = QPen(QColor(200, 200, 200), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        min_x = domain_rect.x() + 0.5
        painter.drawLine(QPointF(min_x, domain_rect.top()), QPointF(min_x, domain_rect.bottom()))
        
        mid_x = domain_rect.x() + domain_rect.width() / 2 + 0.5
        painter.drawLine(QPointF(mid_x, domain_rect.top()), QPointF(mid_x, domain_rect.bottom()))
        
        max_x = domain_rect.x() + domain_rect.width() + 0.5
        painter.drawLine(QPointF(max_x, domain_rect.top()), QPointF(max_x, domain_rect.bottom()))
        
        # Draw line graph
        data_range = self._max_value - self._min_value
        painter.setPen(QPen(self._color, 1))
        
        num_points = len(self._data)
        height_per_point = domain_rect.height() / num_points if num_points > 1 else domain_rect.height()
        
        points = []
        for i, value in enumerate(self._data):
            normalized = (value - self._min_value) / data_range
            normalized = max(0.0, min(1.0, normalized))
            
            x = domain_rect.x() + (normalized * domain_rect.width())
            y = domain_rect.y() + (i * height_per_point)
            
            points.append(QPointF(x, y))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])


# =============================================================================
# LayerColumn
# =============================================================================

@dataclass
class LayerStyle:
    """Visual style for a layer category."""
    color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    pattern_svg: str | None = None
    text_align: str = "center"


class LayerColumn(BaseColumn):
    """
    Column for displaying discrete stratigraphic layers.
    
    Flexible design:
    - Column defines categories (legend) with visual styles
    - Column stores which category applies to each row
    - Each row renders with its assigned category's style
    - Supports: background colors, SVG patterns, text with alignment
    - Supports dynamic color calculation via callback
    """
    
    def __init__(
        self,
        title: str,
        categories: dict[str, LayerStyle] | None = None,
        width: int = 150,
        auto_number: bool = False,
        auto_thickness: bool = False,
        color_callback: Callable[[StratRow], QColor] | None = None,
        hide_text: bool = False
    ) -> None:
        """
        Initialize layer column.
        
        Args:
            title: Column header title
            categories: Dict of category_name -> LayerStyle
            width: Relative width weight
            auto_number: If True, automatically number rows sequentially
            auto_thickness: If True, automatically show row thickness
            color_callback: Optional function that takes a StratRow and returns a QColor
            hide_text: If True, never display text (only background color)
        """
        super().__init__(title, width)
        self.categories: dict[str, LayerStyle] = categories or {}
        self.row_assignments: dict[str, str] = {}
        self.row_text: dict[str, str] = {}
        self._svg_renderers: dict[str, QSvgRenderer] = {}
        self.auto_number = auto_number
        self.auto_thickness = auto_thickness
        self.color_callback = color_callback
        self.hide_text = hide_text
    
    def add_category(self, name: str, style: LayerStyle) -> None:
        """Add or update a category."""
        self.categories[name] = style
        if name in self._svg_renderers:
            del self._svg_renderers[name]
    
    def set_row_category(self, row_id: str, category_name: str, display_text: str | None = None) -> None:
        """Assign a category to a row."""
        if category_name not in self.categories:
            raise ValueError(f"Category '{category_name}' not defined")
        self.row_assignments[row_id] = category_name
        if display_text is not None:
            self.row_text[row_id] = display_text
    
    def get_row_category(self, row_id: str) -> str | None:
        """Get the category assigned to a row."""
        return self.row_assignments.get(row_id)
    
    def clear_row_category(self, row_id: str) -> None:
        """Clear the category assignment for a row."""
        if row_id in self.row_assignments:
            del self.row_assignments[row_id]
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Layer columns don't define height - rows do."""
        return 0.0
    
    def paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """Paint layers with their assigned styles."""
        if not rows:
            return
        
        for row_index, row in enumerate(rows):
            # Use color callback if provided (dynamic color mode)
            if self.color_callback:
                row_color = self.color_callback(row)
                display_text = None
                pattern_svg = None
                text_align = "center"
            # Auto-number mode
            elif self.auto_number:
                category_name = next(iter(self.categories.keys()), None) if self.categories else None
                if not category_name or category_name not in self.categories:
                    continue
                style = self.categories[category_name]
                row_color = style.color
                pattern_svg = style.pattern_svg
                text_align = style.text_align
                display_text = str(row_index + 1)
            # Auto-thickness mode
            elif self.auto_thickness:
                category_name = next(iter(self.categories.keys()), None) if self.categories else None
                if not category_name or category_name not in self.categories:
                    continue
                style = self.categories[category_name]
                row_color = style.color
                pattern_svg = style.pattern_svg
                text_align = style.text_align
                thickness = row.max_depth - row.min_depth
                display_text = f"{thickness:.1f} mm"
            # Manual assignment mode
            else:
                category_name = self.row_assignments.get(row.id)
                if not category_name or category_name not in self.categories:
                    continue
                style = self.categories[category_name]
                row_color = style.color
                pattern_svg = style.pattern_svg
                text_align = style.text_align
                display_text = self.row_text.get(row.id, category_name)
            
            # Calculate row rectangle
            y_top = self._depth_to_pixel(row.min_depth, rect, depth_range)
            y_bottom = self._depth_to_pixel(row.max_depth, rect, depth_range)
            
            # Skip if not visible
            if y_bottom < rect.top() or y_top > rect.bottom():
                continue
            
            y_top = max(y_top, rect.top())
            y_bottom = min(y_bottom, rect.bottom())
            
            row_rect = QRectF(rect.x(), y_top, rect.width(), y_bottom - y_top)
            
            # Draw background color
            painter.fillRect(row_rect, row_color)
            
            # Draw SVG pattern if provided
            if pattern_svg:
                self._draw_pattern(painter, row_rect, category_name if not self.color_callback else "dynamic", pattern_svg)
            
            # Draw text - only if not hidden and rectangle has minimum size
            if not self.hide_text and display_text and row_rect.width() >= 20 and row_rect.height() >= 12:
                self._draw_text(painter, row_rect, display_text, text_align)
    
    def _draw_pattern(self, painter: QPainter, rect: QRectF, category_name: str, pattern_svg: str) -> None:
        """Draw SVG pattern in the rectangle."""
        if category_name not in self._svg_renderers:
            renderer = QSvgRenderer()
            if renderer.load(pattern_svg.encode('utf-8')):
                self._svg_renderers[category_name] = renderer
            else:
                return
        
        renderer = self._svg_renderers[category_name]
        renderer.render(painter, rect)
    
    def _draw_text(self, painter: QPainter, rect: QRectF, text: str, alignment: str) -> None:
        """Draw text in the rectangle with specified alignment."""
        painter.save()
        painter.setPen(Qt.black)
        
        if alignment == "top-left":
            text_rect = rect.adjusted(5, 5, -5, -5)
            qt_align = Qt.AlignLeft | Qt.AlignTop
        else:
            text_rect = rect
            qt_align = Qt.AlignCenter
        
        painter.drawText(text_rect, qt_align, text)
        painter.restore()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Types
    'StratRow',
    'LayerStyle',
    # Functions
    'rows_from_layers',
    # Classes
    'BaseColumn',
    'ImageColumn',
    'RulerColumn',
    'DataColumn',
    'LayerColumn',
    # Constants
    'HEADER_HEIGHT',
    'TITLE_HEIGHT',
    'HEADER_GAP',
    'DOMAIN_PADDING',
]
