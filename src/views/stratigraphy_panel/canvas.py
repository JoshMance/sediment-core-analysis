from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPaintEvent, QPen, QFont
from PySide6.QtCore import Qt, QRectF
from .column import HEADER_HEIGHT, TITLE_HEIGHT

class StratigraphyCanvas(QWidget):
    """Canvas widget for displaying stratigraphy data."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        
        # Column list
        self.columns = []
        
        # Title
        self.title = "Stratigraphy Log"
        
        # Depth range (for now, arbitrary units)
        self.depth_range = (0.0, 100.0)
        
        # Scroll state
        self.scroll_offset = 0.0
        self.max_content_height = 0.0
        
        # Panning state
        self.is_panning = False
        self.last_pan_pos = None
        
    def add_column(self, column) -> None:
        """Add a column to the canvas."""
        self.columns.append(column)
        self._update_scroll_range()
        self.update()
    
    def set_columns(self, columns: list) -> None:
        """Set all columns at once."""
        self.columns = columns
        self._update_scroll_range()
        self.update()
    
    def set_title(self, title: str) -> None:
        """Set the title text."""
        self.title = title
        self.update()
    
    def _update_scroll_range(self) -> None:
        """Calculate maximum content height from all columns."""
        if not self.columns:
            self.max_content_height = 0.0
            return
        
        # Calculate total width weight
        total_weight = sum(col.width for col in self.columns)
        canvas_width = self.width()
        
        # Find the tallest column content
        max_height = 0.0
        for column in self.columns:
            actual_width = (column.width / total_weight) * canvas_width
            content_height = column.get_content_height(actual_width, self.depth_range)
            max_height = max(max_height, content_height)
        
        self.max_content_height = max_height
    
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for scrolling."""
        # Get scroll delta (positive = scroll up, negative = scroll down)
        delta = event.angleDelta().y()
        scroll_amount = -delta / 2  # Convert to pixels (faster scrolling)
        
        # Update scroll offset with bounds checking
        available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
        max_scroll = max(0.0, self.max_content_height - available_height)
        
        self.scroll_offset = max(0.0, min(self.scroll_offset + scroll_amount, max_scroll))
        self.update()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for panning."""
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for panning."""
        if self.is_panning and self.last_pan_pos is not None:
            # Calculate delta
            delta_y = event.pos().y() - self.last_pan_pos.y()
            self.last_pan_pos = event.pos()
            
            # Update scroll offset (opposite direction of mouse movement)
            available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
            max_scroll = max(0.0, self.max_content_height - available_height)
            
            self.scroll_offset = max(0.0, min(self.scroll_offset - delta_y, max_scroll))
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to stop panning."""
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
    
    def resizeEvent(self, event) -> None:
        """Handle resize to recalculate scroll range."""
        super().resizeEvent(event)
        self._update_scroll_range()
        
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the canvas with all columns."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        
        if not self.columns:
            painter.end()
            return
        
        canvas_width = self.width()
        canvas_height = self.height()
        
        # Draw title section at the very top
        title_rect = QRectF(0, 0, canvas_width, TITLE_HEIGHT)
        painter.fillRect(title_rect, Qt.white)
        
        # Draw title borders (left, top, right only - no bottom to avoid double line)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(0, 0, int(canvas_width), 0)  # Top
        painter.drawLine(0, 0, 0, int(TITLE_HEIGHT))  # Left
        painter.drawLine(int(canvas_width), 0, int(canvas_width), int(TITLE_HEIGHT))  # Right
        
        # Draw title text (normal size)
        painter.drawText(title_rect.adjusted(10, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        
        # Calculate total width weight
        total_weight = sum(col.width for col in self.columns)
        
        # Draw left border (starting below title)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(0, int(TITLE_HEIGHT), 0, canvas_height)
        
        # Calculate actual pixel widths proportionally
        x_offset = 0
        
        for i, column in enumerate(self.columns):
            # Calculate this column's actual pixel width based on weight
            actual_width = (column.width / total_weight) * canvas_width
            
            # Define the rect for this column (offset by title height)
            column_rect = QRectF(x_offset, TITLE_HEIGHT, actual_width, canvas_height - TITLE_HEIGHT)
            
            # Let the column paint itself with scroll offset
            column.paint(painter, column_rect, self.depth_range, self.scroll_offset)
            
            # Move to next column
            x_offset += actual_width
            
            # Draw vertical separator line after each column (starting below title)
            painter.setPen(QPen(Qt.black, 1))
            painter.drawLine(int(x_offset), int(TITLE_HEIGHT), int(x_offset), canvas_height)
        
        painter.end()
