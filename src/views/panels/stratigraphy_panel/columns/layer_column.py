"""Layer column for displaying discrete stratigraphic intervals."""

from dataclasses import dataclass, field
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import QRectF, Qt
from PySide6.QtSvg import QSvgRenderer
from .base import BaseColumn
from ..rows import StratRow


@dataclass
class LayerStyle:
    """Visual style for a layer category."""
    color: QColor = field(default_factory=lambda: QColor(255, 255, 255))  # Background color
    pattern_svg: str | None = None  # Optional SVG pattern
    text_align: str = "center"  # "center" or "top-left"
    

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
        color_callback=None,  # Callable[[StratRow], QColor] - dynamically calculate color per row
        hide_text: bool = False  # If True, don't display any text
    ) -> None:
        """
        Initialize layer column.
        
        Args:
            title: Column header title
            categories: Dict of category_name -> LayerStyle
            width: Relative width weight
            auto_number: If True, automatically number rows sequentially (1, 2, 3...)
            auto_thickness: If True, automatically show row thickness (depth span in mm)
            color_callback: Optional function that takes a StratRow and returns a QColor
            hide_text: If True, never display text (only background color)
        """
        super().__init__(title, width)
        self.categories: dict[str, LayerStyle] = categories or {}
        self.row_assignments: dict[str, str] = {}  # row_id -> category_name
        self.row_text: dict[str, str] = {}  # row_id -> custom display text (overrides category name)
        self._svg_renderers: dict[str, QSvgRenderer] = {}  # Cache SVG renderers
        self.auto_number = auto_number  # Enable automatic row numbering
        self.auto_thickness = auto_thickness  # Enable automatic thickness display
        self.color_callback = color_callback  # Dynamic color calculation
        self.hide_text = hide_text  # Option to hide all text
    
    def add_category(self, name: str, style: LayerStyle) -> None:
        """Add or update a category."""
        self.categories[name] = style
        # Clear cached renderer if pattern changed
        if name in self._svg_renderers:
            del self._svg_renderers[name]
    
    def set_row_category(self, row_id: str, category_name: str, display_text: str | None = None) -> None:
        """
        Assign a category to a row.
        
        Args:
            row_id: Row identifier
            category_name: Category to assign
            display_text: Optional custom text to display (overrides category name)
        """
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
        """
        Paint layers with their assigned styles.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already clipped and scroll-adjusted)
            depth_range: (min_depth, max_depth) in depth units
            rows: List of depth intervals to render
        """
        if not rows:
            return
        
        for row_index, row in enumerate(rows):
            # Use color callback if provided (dynamic color mode)
            if self.color_callback:
                row_color = self.color_callback(row)
                display_text = None  # No text in dynamic color mode
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
                display_text = str(row_index + 1)  # 1-based numbering
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
                display_text = f"{thickness:.1f} mm"  # Format with unit
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
            
            # Clamp to visible area
            y_top = max(y_top, rect.top())
            y_bottom = min(y_bottom, rect.bottom())
            
            row_rect = QRectF(rect.x(), y_top, rect.width(), y_bottom - y_top)
            
            # Draw background color
            painter.fillRect(row_rect, row_color)
            
            # Draw SVG pattern if provided
            if pattern_svg:
                self._draw_pattern(painter, row_rect, category_name if not self.color_callback else "dynamic", pattern_svg)
            
            # Draw text - only if not hidden and rectangle is wide enough AND tall enough
            # Minimum dimensions: 20px width, 12px height (to fit text)
            if not self.hide_text and display_text and row_rect.width() >= 20 and row_rect.height() >= 12:
                self._draw_text(painter, row_rect, display_text, text_align)
    
    def _draw_pattern(self, painter: QPainter, rect: QRectF, category_name: str, pattern_svg: str) -> None:
        """Draw SVG pattern in the rectangle."""
        # Get or create cached renderer
        if category_name not in self._svg_renderers:
            renderer = QSvgRenderer()
            if renderer.load(pattern_svg.encode('utf-8')):
                self._svg_renderers[category_name] = renderer
            else:
                return  # Invalid SVG
        
        renderer = self._svg_renderers[category_name]
        renderer.render(painter, rect)
    
    def _draw_text(self, painter: QPainter, rect: QRectF, text: str, alignment: str) -> None:
        """Draw text in the rectangle with specified alignment."""
        painter.save()
        
        # Set text color (contrasting with background)
        painter.setPen(Qt.black)
        
        # Set alignment
        if alignment == "top-left":
            text_rect = rect.adjusted(5, 5, -5, -5)  # Small padding
            qt_align = Qt.AlignLeft | Qt.AlignTop
        else:  # "center" (default)
            text_rect = rect
            qt_align = Qt.AlignCenter
        
        painter.drawText(text_rect, qt_align, text)
        painter.restore()
