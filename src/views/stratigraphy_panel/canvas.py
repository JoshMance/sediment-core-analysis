from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPaintEvent, QPen, QFont, QColor
from PySide6.QtCore import Qt, QRectF
from .columns import HEADER_HEIGHT, TITLE_HEIGHT
from .rows import StratRow

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
        
        # Rows (depth intervals between dividers)
        self.rows: list[StratRow] = []
        
        # Scroll state
        self.scroll_offset = 0.0
        self.max_content_height = 0.0
        self.scroll_changed = None  # Callback for scroll updates: (offset, max_offset, page_size)
        
        # Panning state
        self.is_panning = False
        self.last_pan_pos = None
        
        # Divider dragging state
        self.dragging_divider: int | None = None  # Index of row whose max is being dragged
        self.divider_hover: int | None = None  # Index of hovered divider
        self.row_hover: int | None = None  # Index of hovered row area
        self.setMouseTracking(True)  # Enable hover detection
        
        # Interaction mode: None, 'add', or 'delete'
        self.interaction_mode: str | None = None
        
        # Add mode preview line Y position
        self.preview_y: float | None = None
        
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
    
    def set_interaction_mode(self, mode: str | None) -> None:
        """Set the interaction mode ('add', 'delete', or None)."""
        self.interaction_mode = mode
        self.setCursor(Qt.ArrowCursor)
        self.update()
    
    def set_scroll_offset(self, offset: float) -> None:
        """Set scroll offset programmatically (e.g., from scrollbar)."""
        available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
        max_scroll = max(0.0, self.max_content_height - available_height)
        self.scroll_offset = max(0.0, min(offset, max_scroll))
        self.update()
    
    def add_row_divider(self, depth: float) -> None:
        """
        Add a divider at the specified depth, creating/updating rows.
        
        Args:
            depth: Depth value where divider should be placed
        """
        # Find where to insert this depth
        divider_depths = [self.depth_range[0]]
        for row in self.rows:
            divider_depths.append(row.max_depth)
        divider_depths.append(self.depth_range[1])
        
        # Insert new depth (keep sorted, avoid duplicates)
        if depth not in divider_depths:
            divider_depths.append(depth)
            divider_depths.sort()
        
        # Rebuild rows from dividers
        self.rows = []
        for i in range(len(divider_depths) - 1):
            row = StratRow(
                id=f"row_{i}",
                min_depth=divider_depths[i],
                max_depth=divider_depths[i + 1]
            )
            self.rows.append(row)
        
        self.update()
    
    def _delete_divider(self, divider_idx: int) -> None:
        """
        Delete a divider, merging adjacent rows.
        
        Args:
            divider_idx: Index of the row whose max_depth is the divider to delete
        """
        if divider_idx < 0 or divider_idx >= len(self.rows) - 1:
            return  # Can't delete first or last boundary
        
        # Merge rows[divider_idx] and rows[divider_idx + 1]
        merged_row = StratRow(
            id=f"row_{divider_idx}",
            min_depth=self.rows[divider_idx].min_depth,
            max_depth=self.rows[divider_idx + 1].max_depth
        )
        
        # Replace with merged row
        self.rows[divider_idx] = merged_row
        del self.rows[divider_idx + 1]
        
        # Renumber remaining rows
        for i, row in enumerate(self.rows):
            row.id = f"row_{i}"
        
        self.divider_hover = None
        self.update()
    
    def _depth_to_pixel_y(self, depth: float) -> float:
        """
        Convert depth to Y pixel coordinate in content area.
        
        Args:
            depth: Depth value to convert
            
        Returns:
            Y pixel coordinate (including title/header offset and scroll)
        """
        if self.depth_range[1] == self.depth_range[0]:
            return TITLE_HEIGHT + HEADER_HEIGHT
        
        normalized = (depth - self.depth_range[0]) / (self.depth_range[1] - self.depth_range[0])
        content_y = normalized * self.max_content_height
        return TITLE_HEIGHT + HEADER_HEIGHT + content_y - self.scroll_offset
    
    def _pixel_y_to_depth(self, y: float) -> float:
        """
        Convert Y pixel coordinate to depth value.
        
        Args:
            y: Y pixel coordinate
            
        Returns:
            Depth value
        """
        # Remove title/header offset and add scroll offset
        content_y = y - TITLE_HEIGHT - HEADER_HEIGHT + self.scroll_offset
        
        if self.max_content_height == 0:
            return self.depth_range[0]
        
        normalized = content_y / self.max_content_height
        return self.depth_range[0] + (normalized * (self.depth_range[1] - self.depth_range[0]))
    
    def _find_divider_at_position(self, y: float, tolerance: float = 5.0) -> int | None:
        """
        Find divider index near the given Y position.
        
        Args:
            y: Y pixel coordinate
            tolerance: Pixel distance tolerance
            
        Returns:
            Index of row whose max_depth divider is near Y, or None
        """
        for i in range(len(self.rows) - 1):  # Exclude last row (bottom boundary)
            divider_y = self._depth_to_pixel_y(self.rows[i].max_depth)
            if abs(y - divider_y) <= tolerance:
                return i
        return None
    
    def _update_scroll_range(self) -> None:
        """Calculate maximum content height from all columns."""
        if not self.columns:
            self.max_content_height = 0.0
            return
        
        # Calculate total width weight
        total_weight = sum(col.width for col in self.columns)
        canvas_width = self.width()
        
        # Find scale-defining column (if any)
        scale_column = None
        for column in self.columns:
            if column.provides_scale():
                scale_column = column
                break
        
        # If we have a scale-defining column, use its scale as canonical
        if scale_column:
            actual_width = (scale_column.width / total_weight) * canvas_width
            scale_info = scale_column.get_scale(actual_width)
            if scale_info:
                pixel_height, depth_range = scale_info
                self.max_content_height = pixel_height
                self.depth_range = depth_range  # Update canvas depth range
                return
        
        # Otherwise, find the tallest column content
        max_height = 0.0
        for column in self.columns:
            actual_width = (column.width / total_weight) * canvas_width
            content_height = column.get_content_height(actual_width, self.depth_range)
            max_height = max(max_height, content_height)
        
        self.max_content_height = max_height
        
        # Notify scrollbar of potential change
        if self.scroll_changed:
            available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
            max_scroll = max(0.0, self.max_content_height - available_height)
            self.scroll_changed(self.scroll_offset, max_scroll, available_height)
    
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for scrolling."""
        # Get scroll delta (positive = scroll up, negative = scroll down)
        delta = event.angleDelta().y()
        scroll_amount = -delta / 2  # Convert to pixels (faster scrolling)
        
        # Update scroll offset with bounds checking
        available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
        max_scroll = max(0.0, self.max_content_height - available_height)
        
        self.scroll_offset = max(0.0, min(self.scroll_offset + scroll_amount, max_scroll))
        
        # Notify scrollbar of change
        if self.scroll_changed:
            self.scroll_changed(self.scroll_offset, max_scroll, available_height)
        
        self.update()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for divider dragging, add/delete modes, or panning."""
        if event.button() == Qt.LeftButton:
            y = event.pos().y()
            
            # Add mode: click in chart area to add divider
            if self.interaction_mode == 'add':
                # Only add if clicking in chart area (below header)
                if y > TITLE_HEIGHT + HEADER_HEIGHT:
                    depth = self._pixel_y_to_depth(y)
                    # Clamp to depth range
                    depth = max(self.depth_range[0], min(depth, self.depth_range[1]))
                    self.add_row_divider(depth)
                return
            
            # Delete mode: click on divider to delete it
            if self.interaction_mode == 'delete':
                divider_idx = self._find_divider_at_position(y)
                if divider_idx is not None:
                    self._delete_divider(divider_idx)
                return
            
            # Default mode: check if clicking on a divider for dragging
            divider_idx = self._find_divider_at_position(y)
            if divider_idx is not None:
                self.dragging_divider = divider_idx
                self.setCursor(Qt.SizeVerCursor)
            else:
                # Start panning
                self.is_panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for divider dragging, panning, or hover."""
        if self.dragging_divider is not None:
            # Drag divider
            new_depth = self._pixel_y_to_depth(event.pos().y())
            
            # Clamp to adjacent rows
            idx = self.dragging_divider
            min_limit = self.rows[idx].min_depth + 0.1  # Small gap minimum
            max_limit = self.rows[idx + 1].max_depth - 0.1 if idx + 1 < len(self.rows) else self.depth_range[1]
            
            new_depth = max(min_limit, min(new_depth, max_limit))
            
            # Update adjacent rows
            self.rows[idx].max_depth = new_depth
            self.rows[idx + 1].min_depth = new_depth
            
            self.update()
            
        elif self.is_panning and self.last_pan_pos is not None:
            # Pan viewport
            delta_y = event.pos().y() - self.last_pan_pos.y()
            self.last_pan_pos = event.pos()
            
            # Update scroll offset (opposite direction of mouse movement)
            available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT
            max_scroll = max(0.0, self.max_content_height - available_height)
            
            self.scroll_offset = max(0.0, min(self.scroll_offset - delta_y, max_scroll))
            
            # Notify scrollbar of change
            if self.scroll_changed:
                self.scroll_changed(self.scroll_offset, max_scroll, available_height)
            
            self.update()
        else:
            # Update hover state for cursor (skip if in add mode)
            if self.interaction_mode == 'add':
                # Track preview position for add mode
                y = event.pos().y()
                if y > TITLE_HEIGHT + HEADER_HEIGHT:
                    self.preview_y = y
                else:
                    self.preview_y = None
                
                # Clear divider hover in add mode
                if self.divider_hover is not None:
                    self.divider_hover = None
                self.update()
            else:
                # Clear preview if not in add mode
                if self.preview_y is not None:
                    self.preview_y = None
                
                divider_idx = self._find_divider_at_position(event.pos().y())
                
                # Check if hovering over a row area (not on a divider)
                row_idx = None
                if divider_idx is None and self.rows:
                    y = event.pos().y()
                    if y > TITLE_HEIGHT + HEADER_HEIGHT:
                        depth = self._pixel_y_to_depth(y)
                        # Find which row contains this depth
                        for i, row in enumerate(self.rows):
                            if row.min_depth <= depth <= row.max_depth:
                                row_idx = i
                                break
                
                # Update hover states
                needs_update = False
                if divider_idx != self.divider_hover:
                    self.divider_hover = divider_idx
                    needs_update = True
                if row_idx != self.row_hover:
                    self.row_hover = row_idx
                    needs_update = True
                
                if needs_update:
                    # Set cursor based on mode and hover state
                    if self.divider_hover is not None:
                        if self.interaction_mode == 'delete':
                            self.setCursor(Qt.PointingHandCursor)
                        elif self.interaction_mode is None:
                            self.setCursor(Qt.PointingHandCursor)
                    elif self.row_hover is not None:
                        self.setCursor(Qt.PointingHandCursor)
                    else:
                        self.setCursor(Qt.ArrowCursor)
                    self.update()  # Redraw to show hover color
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to stop dragging/panning."""
        if event.button() == Qt.LeftButton:
            if self.dragging_divider is not None:
                self.dragging_divider = None
            else:
                self.is_panning = False
                self.last_pan_pos = None
            
            # Update cursor based on position
            divider_idx = self._find_divider_at_position(event.pos().y())
            if divider_idx is not None:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def resizeEvent(self, event) -> None:
        """Handle resize to recalculate scroll range."""
        super().resizeEvent(event)
        self._update_scroll_range()
        
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the canvas with all columns."""
        painter = QPainter(self)
        # Antialiasing disabled
        # painter.setRenderHint(QPainter.Antialiasing)
        # painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), Qt.white)
        
        # Get device pixel ratio for HiDPI displays
        dpr = self.devicePixelRatio()
        
        if not self.columns:
            painter.end()
            return
        
        canvas_width = self.width()
        canvas_height = self.height()
        
        # Draw title section at the very top
        title_rect = QRectF(0, 0, canvas_width, TITLE_HEIGHT)
        painter.fillRect(title_rect, Qt.white)
        
        # Draw title borders (left, top, right only - no bottom to avoid double line)
        painter.setPen(QPen(QColor(45, 45, 45), max(1, int(1 * dpr))))
        painter.drawLine(0, 0, int(canvas_width), 0)  # Top
        painter.drawLine(0, 0, 0, int(TITLE_HEIGHT))  # Left
        painter.drawLine(int(canvas_width), 0, int(canvas_width), int(TITLE_HEIGHT))  # Right
        
        # Draw title text (normal size)
        painter.drawText(title_rect.adjusted(10, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        
        # Calculate total width weight
        total_weight = sum(col.width for col in self.columns)
        
        # Draw left border (starting below title)
        painter.setPen(QPen(QColor(45, 45, 45), max(1, int(1 * dpr))))
        painter.drawLine(0, int(TITLE_HEIGHT), 0, canvas_height)
        
        # Calculate actual pixel widths proportionally
        x_offset = 0
        
        # Use max_content_height for column rects so all columns have the same vertical scale
        # The visible portion is controlled by scroll_offset and clipping in column.paint()
        content_height = self.max_content_height + HEADER_HEIGHT
        
        for i, column in enumerate(self.columns):
            # Calculate this column's actual pixel width based on weight
            actual_width = (column.width / total_weight) * canvas_width
            
            # Define the rect for this column (offset by title height, full content height)
            column_rect = QRectF(x_offset, TITLE_HEIGHT, actual_width, content_height)
            
            # Let the column paint itself with scroll offset and rows
            column.paint(painter, column_rect, self.depth_range, self.scroll_offset, self.rows)
            
            # Move to next column
            x_offset += actual_width
            
            # Draw vertical separator line after each column (starting below title)
            painter.setPen(QPen(QColor(45, 45, 45), 1))
            painter.drawLine(int(x_offset), int(TITLE_HEIGHT), int(x_offset), canvas_height)
        
        # Draw row hover overlay (before dividers so dividers draw on top)
        if self.row_hover is not None and self.row_hover < len(self.rows):
            row = self.rows[self.row_hover]
            y_top = self._depth_to_pixel_y(row.min_depth)
            y_bottom = self._depth_to_pixel_y(row.max_depth)
            
            # Only draw if visible
            if y_bottom >= TITLE_HEIGHT + HEADER_HEIGHT and y_top <= canvas_height:
                # Clamp to visible area
                visible_top = max(y_top, TITLE_HEIGHT + HEADER_HEIGHT)
                visible_bottom = min(y_bottom, canvas_height)
                
                # Draw semi-transparent blue overlay
                painter.fillRect(QRectF(0, visible_top, canvas_width, visible_bottom - visible_top), 
                               QColor(0, 120, 215, 51))  # 20% opacity (51/255)
        
        # Draw horizontal dividers across all columns
        if self.rows:
            for i in range(len(self.rows) - 1):  # Exclude last row (bottom boundary)
                y = self._depth_to_pixel_y(self.rows[i].max_depth)
                # Only draw if visible in viewport
                if TITLE_HEIGHT + HEADER_HEIGHT <= y <= canvas_height:
                    # Check if this divider should be highlighted (hovered directly, or part of hovered row)
                    is_highlighted = (i == self.divider_hover or 
                                    (self.row_hover is not None and (i == self.row_hover or i == self.row_hover - 1)))
                    
                    # Red if delete mode + hovered, blue if highlighted, dark grey otherwise
                    if i == self.divider_hover and self.interaction_mode == 'delete':
                        painter.setPen(QPen(QColor(220, 50, 50), 2))  # Red, 2px
                    elif is_highlighted:
                        painter.setPen(QPen(QColor(0, 120, 215), 2))  # Blue, 2px
                    else:
                        painter.setPen(QPen(QColor(80, 80, 80), 1))  # Dark grey, 1px
                    painter.drawLine(0, int(y), canvas_width, int(y))
        
        # Draw preview line in add mode
        if self.interaction_mode == 'add' and self.preview_y is not None:
            painter.setPen(QPen(QColor(180, 180, 180), 1))  # Light grey, 1px
            painter.drawLine(0, int(self.preview_y), canvas_width, int(self.preview_y))
        
        painter.end()
