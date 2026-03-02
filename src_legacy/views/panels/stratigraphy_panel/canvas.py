from __future__ import annotations
from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPaintEvent, QPen, QFont, QColor
from PySide6.QtCore import Qt, QRectF, QPointF
from .columns import HEADER_HEIGHT, TITLE_HEIGHT, HEADER_GAP, StratRow, rows_from_layers

if TYPE_CHECKING:
    from models import CoreAnalysis


class StratigraphyCanvas(QWidget):
    """
    Canvas widget for displaying stratigraphy data.
    
    The canvas RENDERS data from a CoreAnalysis - it does NOT own layer state.
    When user interactions occur, the canvas emits callbacks instead of
    mutating state. The controller (demo) handles callbacks, updates the
    entity via services, and calls refresh() to update the view.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        
        # Column list
        self.columns = []
        
        # Title
        self.title = "Stratigraphy Log"
        
        # Depth range (for now, arbitrary units)
        self.depth_range = (0.0, 100.0)
        
        # Analysis reference (authoritative layer state lives here)
        self._analysis: CoreAnalysis | None = None
        
        # Cached rows computed from analysis (read-only rendering hints)
        self._cached_rows: list[StratRow] = []
        
        # Callbacks for boundary operations (set by controller/demo)
        self.on_boundary_add: Callable[[float], None] | None = None  # depth in mm
        self.on_boundary_delete: Callable[[int], None] | None = None  # layer index
        self.on_boundary_move: Callable[[int, float], None] | None = None  # divider index, new_depth
        
        # Scroll state
        self.scroll_offset = 0.0
        self.max_content_height = 0.0
        self.scroll_changed = None  # Callback for scroll updates: (offset, max_offset, page_size)
        
        # Panning state
        self.is_panning = False
        self.last_pan_pos = None
        
        # Divider dragging state
        self.dragging_divider: int | None = None  # Index of divider being dragged
        self._drag_preview_depth: float | None = None  # Preview depth during drag
        self.divider_hover: int | None = None  # Index of hovered divider
        self.row_hover: int | None = None  # Index of hovered row area
        self.setMouseTracking(True)  # Enable hover detection
        
        # Interaction mode: None, 'add', or 'delete'
        self.interaction_mode: str | None = None
        
        # Add mode preview line Y position
        self.preview_y: float | None = None
    
    @property
    def rows(self) -> list[StratRow]:
        """Get rows for rendering (computed from analysis or cached)."""
        return self._cached_rows
    
    def set_analysis(self, analysis: CoreAnalysis) -> None:
        """
        Set the analysis to render.
        
        Rows are computed from analysis.layers. The view does NOT own
        the layer state - CoreAnalysis is the authoritative source.
        """
        self._analysis = analysis
        self._refresh_rows()
        self._update_scroll_range()
        self.update()
    
    def refresh(self) -> None:
        """Recompute rows from analysis and repaint. Call after entity changes."""
        self._refresh_rows()
        self._update_scroll_range()
        self.update()
    
    def _refresh_rows(self) -> None:
        """Recompute cached rows from analysis."""
        if self._analysis is None:
            self._cached_rows = []
        else:
            self._cached_rows = rows_from_layers(
                self._analysis.layers,
                self._analysis.core,
            )
        
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
        available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT - HEADER_GAP
        max_scroll = max(0.0, self.max_content_height - available_height)
        self.scroll_offset = max(0.0, min(offset, max_scroll))
        self.update()
    
    def _request_add_boundary(self, depth: float) -> None:
        """
        Request adding a boundary at the specified depth.
        
        Invokes the on_boundary_add callback if set. The controller
        is responsible for actually modifying the analysis via services
        and calling refresh().
        
        Args:
            depth: Depth value where boundary should be placed (in mm)
        """
        if self.on_boundary_add is not None:
            self.on_boundary_add(depth)
    
    def _request_delete_boundary(self, divider_idx: int) -> None:
        """
        Request deleting the boundary at the given divider index.
        
        Invokes the on_boundary_delete callback if set. The controller
        is responsible for actually modifying the analysis via services
        and calling refresh().
        
        Args:
            divider_idx: Index of the divider to delete (boundary between layer[i] and layer[i+1])
        """
        if self.on_boundary_delete is not None:
            self.on_boundary_delete(divider_idx)
    
    def _request_move_boundary(self, divider_idx: int, new_depth: float) -> None:
        """
        Request moving a boundary to a new depth.
        
        Invokes the on_boundary_move callback if set. The controller
        is responsible for actually modifying the analysis via services
        and calling refresh().
        
        Args:
            divider_idx: Index of the divider being moved
            new_depth: New depth for the boundary (in mm)
        """
        if self.on_boundary_move is not None:
            self.on_boundary_move(divider_idx, new_depth)
    
    def _depth_to_pixel_y(self, depth: float) -> float:
        """
        Convert depth to Y pixel coordinate in content area.
        
        Args:
            depth: Depth value to convert
            
        Returns:
            Y pixel coordinate (including title/header offset and scroll)
        """
        if self.depth_range[1] == self.depth_range[0]:
            return TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP
        
        normalized = (depth - self.depth_range[0]) / (self.depth_range[1] - self.depth_range[0])
        content_y = normalized * self.max_content_height
        return TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP + content_y - self.scroll_offset
    
    def _pixel_y_to_depth(self, y: float) -> float:
        """
        Convert Y pixel coordinate to depth value.
        
        Args:
            y: Y pixel coordinate
            
        Returns:
            Depth value
        """
        # Remove title/header/gap offset and add scroll offset
        content_y = y - TITLE_HEIGHT - HEADER_HEIGHT - HEADER_GAP + self.scroll_offset
        
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
    
    def _paint_column_header(self, painter: QPainter, rect: QRectF, column, dpr: float) -> None:
        """
        Paint a column header with title and optional metadata.
        
        Canvas draws borders separately as continuous lines across all headers.
        
        Args:
            painter: QPainter to draw with
            rect: Header rectangle
            column: Column object with title and metadata
            dpr: Device pixel ratio for HiDPI displays
        """
        # Draw header background
        painter.fillRect(rect, Qt.white)
        
        # Get column metadata
        metadata = column.get_header_metadata()
        
        # Draw title (default centered)
        if 'unit' in metadata:
            # For rulers: title on first line, unit in brackets on second line
            title_rect = rect.adjusted(2, 5, -2, -HEADER_HEIGHT/2)
            painter.setPen(Qt.black)
            painter.drawText(title_rect, Qt.AlignCenter | Qt.AlignBottom, column.title)
            
            unit_rect = rect.adjusted(2, HEADER_HEIGHT/2, -2, -5)
            painter.setPen(Qt.gray)
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(unit_rect, Qt.AlignCenter | Qt.AlignTop, f"({metadata['unit']})")
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(Qt.black)
        elif 'domain_range' in metadata:
            # For data columns: title centered, domain line below
            painter.drawText(rect, Qt.AlignCenter, column.title)
            
            painter.save()
            min_val, max_val = metadata['domain_range']
            domain_line_y = rect.bottom() - 16 + 0.5  # Horizontal: y + 0.5
            
            # Draw domain line (inset by padding)
            from .columns import DOMAIN_PADDING
            pen = QPen(QColor(100, 100, 100), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            line_x1 = rect.x() + DOMAIN_PADDING
            line_x2 = rect.x() + rect.width() - DOMAIN_PADDING
            painter.drawLine(QPointF(line_x1, domain_line_y), QPointF(line_x2, domain_line_y))
            
            # Draw min/max values
            painter.setPen(QColor(80, 80, 80))
            font = painter.font()
            font.setPointSize(7)
            painter.setFont(font)
            
            # Format as percentage if in 0-1 range
            is_percentage = (min_val >= 0 and max_val <= 1)
            min_text = f"{int(min_val * 100)}%" if is_percentage else f"{min_val:.2f}"
            max_text = f"{int(max_val * 100)}%" if is_percentage else f"{max_val:.2f}"
            
            text_y = domain_line_y + 2
            text_height = min(12, rect.bottom() - text_y)
            
            min_rect = QRectF(line_x1, text_y, 50, text_height)
            painter.drawText(min_rect, Qt.AlignLeft | Qt.AlignTop, min_text)
            
            max_rect = QRectF(line_x2 - 50, text_y, 50, text_height)
            painter.drawText(max_rect, Qt.AlignRight | Qt.AlignTop, max_text)
            
            painter.restore()
        else:
            # Default: simple centered title
            painter.drawText(rect, Qt.AlignCenter, column.title)
    
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
            available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT - HEADER_GAP
            max_scroll = max(0.0, self.max_content_height - available_height)
            self.scroll_changed(self.scroll_offset, max_scroll, available_height)
    
    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for scrolling."""
        # Get scroll delta (positive = scroll up, negative = scroll down)
        delta = event.angleDelta().y()
        scroll_amount = -delta / 2  # Convert to pixels (faster scrolling)
        
        # Update scroll offset with bounds checking
        available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT - HEADER_GAP
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
            
            # Add mode: click in chart area to request adding a boundary
            if self.interaction_mode == 'add':
                # Only add if clicking in chart area (below header)
                if y > TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP:
                    depth = self._pixel_y_to_depth(y)
                    # Clamp to depth range
                    depth = max(self.depth_range[0], min(depth, self.depth_range[1]))
                    self._request_add_boundary(depth)
                return
            
            # Delete mode: click on divider to request deleting it
            if self.interaction_mode == 'delete':
                divider_idx = self._find_divider_at_position(y)
                if divider_idx is not None:
                    self._request_delete_boundary(divider_idx)
                return
            
            # Default mode: check if clicking on a divider for dragging
            divider_idx = self._find_divider_at_position(y)
            if divider_idx is not None:
                self.dragging_divider = divider_idx
                # Initialize drag preview with current boundary depth
                if divider_idx < len(self.rows):
                    self._drag_preview_depth = self.rows[divider_idx].max_depth
                self.setCursor(Qt.SizeVerCursor)
            else:
                # Start panning
                self.is_panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for divider dragging, panning, or hover."""
        if self.dragging_divider is not None:
            # Drag divider - update preview depth (visual feedback)
            new_depth = self._pixel_y_to_depth(event.pos().y())
            
            # Clamp to adjacent rows
            idx = self.dragging_divider
            if idx < len(self.rows) and idx + 1 < len(self.rows):
                min_limit = self.rows[idx].min_depth + 0.1  # Small gap minimum
                max_limit = self.rows[idx + 1].max_depth - 0.1
                new_depth = max(min_limit, min(new_depth, max_limit))
            
            # Update preview depth for visual feedback
            self._drag_preview_depth = new_depth
            self.update()
            
        elif self.is_panning and self.last_pan_pos is not None:
            # Pan viewport
            delta_y = event.pos().y() - self.last_pan_pos.y()
            self.last_pan_pos = event.pos()
            
            # Update scroll offset (opposite direction of mouse movement)
            available_height = self.height() - TITLE_HEIGHT - HEADER_HEIGHT - HEADER_GAP
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
                if y > TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP:
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
                    if y > TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP:
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
                # Drag completed - emit callback with final position
                if self._drag_preview_depth is not None:
                    self._request_move_boundary(self.dragging_divider, self._drag_preview_depth)
                
                # Clear drag state
                self.dragging_divider = None
                self._drag_preview_depth = None
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
        painter.fillRect(self.rect(), Qt.white)  # White background for content area
        
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
        pen = QPen(QColor(45, 45, 45), 1)
        pen.setCosmetic(True)  # Always 1 physical pixel
        painter.setPen(pen)
        painter.drawLine(0, 0.5, int(canvas_width), 0.5)  # Top (horizontal: y + 0.5)
        painter.drawLine(0.5, 0, 0.5, int(TITLE_HEIGHT))  # Left (vertical: x + 0.5)
        painter.drawLine(int(canvas_width) - 0.5, 0, int(canvas_width) - 0.5, int(TITLE_HEIGHT))  # Right (vertical: x + 0.5)
        
        # Draw title text (normal size)
        painter.drawText(title_rect.adjusted(10, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, self.title)
        
        # Calculate column layout
        total_weight = sum(col.width for col in self.columns)
        column_x_positions = [0.0]  # Starting x positions for each column
        x = 0.0
        for col in self.columns:
            x += (col.width / total_weight) * canvas_width
            column_x_positions.append(round(x))  # Round to nearest pixel for consistent alignment
        
        # Draw all column headers FIRST (backgrounds and content, no borders)
        for i, column in enumerate(self.columns):
            x_start = column_x_positions[i]
            x_end = column_x_positions[i + 1]
            header_rect = QRectF(x_start, TITLE_HEIGHT, x_end - x_start, HEADER_HEIGHT)
            self._paint_column_header(painter, header_rect, column, dpr)
        
        # Draw ALL structural lines ON TOP (so they're not covered by header backgrounds)
        pen = QPen(QColor(45, 45, 45), 1)
        pen.setCosmetic(True)  # Always 1 physical pixel
        painter.setPen(pen)
        
        # Fill the gap area with grey
        gap_rect = QRectF(0, TITLE_HEIGHT + HEADER_HEIGHT, canvas_width, HEADER_GAP)
        painter.fillRect(gap_rect, QColor(240, 240, 240))
        
        # Horizontal header lines (across full width) - offset by 0.5 for crispness
        header_top_y = int(TITLE_HEIGHT) + 0.5
        header_bottom_y = int(TITLE_HEIGHT + HEADER_HEIGHT) + 0.5
        content_top_y = int(TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP) + 0.5
        painter.drawLine(0, header_top_y, canvas_width, header_top_y)
        painter.drawLine(0, header_bottom_y, canvas_width, header_bottom_y)
        painter.drawLine(0, content_top_y, canvas_width, content_top_y)  # Bottom of gap / top of content
        
        # Draw all column content
        content_height = self.max_content_height
        for i, column in enumerate(self.columns):
            x_start = column_x_positions[i]
            x_end = column_x_positions[i + 1]
            width = x_end - x_start
            
            # Content area (below header + gap, with scrolling)
            content_rect = QRectF(x_start, TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP, width, content_height)
            
            # Save painter state and set clipping
            painter.save()
            painter.setClipRect(content_rect)
            
            # Adjust for scroll offset
            scrolled_content_rect = content_rect.translated(0, -self.scroll_offset)
            
            # Let column paint its data
            column.paint_content(painter, scrolled_content_rect, self.depth_range, self.rows)
            
            painter.restore()
        
        # Draw row hover overlay (before dividers so dividers draw on top)
        if self.row_hover is not None and self.row_hover < len(self.rows):
            row = self.rows[self.row_hover]
            y_top = self._depth_to_pixel_y(row.min_depth)
            y_bottom = self._depth_to_pixel_y(row.max_depth)
            
            # Only draw if visible
            if y_bottom >= TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP and y_top <= canvas_height:
                # Clamp to visible area
                visible_top = max(y_top, TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP)
                visible_bottom = min(y_bottom, canvas_height)
                
                # Draw semi-transparent blue overlay
                painter.fillRect(QRectF(0, visible_top, canvas_width, visible_bottom - visible_top), 
                               QColor(0, 120, 215, 51))  # 20% opacity (51/255)
        
        # Draw horizontal dividers across all columns
        if self.rows:
            for i in range(len(self.rows) - 1):  # Exclude last row (bottom boundary)
                # Use preview depth if this divider is being dragged
                if self.dragging_divider == i and self._drag_preview_depth is not None:
                    divider_depth = self._drag_preview_depth
                else:
                    divider_depth = self.rows[i].max_depth
                
                y = self._depth_to_pixel_y(divider_depth)
                # Only draw if visible in viewport
                if TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP <= y <= canvas_height:
                    # Check if this divider should be highlighted (hovered directly, or part of hovered row)
                    is_highlighted = (i == self.divider_hover or 
                                    (self.row_hover is not None and (i == self.row_hover or i == self.row_hover - 1)))
                    
                    # Red if delete mode + hovered, blue if highlighted, dark grey otherwise
                    if i == self.divider_hover and self.interaction_mode == 'delete':
                        pen = QPen(QColor(220, 50, 50), 2)
                        pen.setCosmetic(True)
                        painter.setPen(pen)
                    elif is_highlighted:
                        pen = QPen(QColor(0, 120, 215), 2)
                        pen.setCosmetic(True)
                        painter.setPen(pen)
                    else:
                        pen = QPen(QColor(80, 80, 80), 1)
                        pen.setCosmetic(True)
                        painter.setPen(pen)
                    painter.drawLine(0, int(y) + 0.5, canvas_width, int(y) + 0.5)  # Horizontal: y + 0.5
        
        # Draw preview line in add mode
        if self.interaction_mode == 'add' and self.preview_y is not None:
            pen = QPen(QColor(180, 180, 180), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawLine(0, int(self.preview_y) + 0.5, canvas_width, int(self.preview_y) + 0.5)  # Horizontal: y + 0.5
        
        # Draw vertical column separator lines LAST (on top of all content and dividers)
        pen = QPen(QColor(45, 45, 45), 1)
        pen.setCosmetic(True)  # Always 1 physical pixel
        painter.setPen(pen)
        
        # Draw left border as continuous line (crosses the gap)
        painter.drawLine(0.5, int(TITLE_HEIGHT), 0.5, canvas_height)
        
        # Draw right border as continuous line (crosses the gap)
        painter.drawLine(int(canvas_width) - 0.5, int(TITLE_HEIGHT), int(canvas_width) - 0.5, canvas_height)
        
        # Draw internal column separators in two sections (skip the gap)
        for i, x_pos in enumerate(column_x_positions):
            # Skip first (left border) and last (right border) positions
            if i == 0 or i == len(column_x_positions) - 1:
                continue
            # Header section
            painter.drawLine(x_pos + 0.5, int(TITLE_HEIGHT), x_pos + 0.5, int(TITLE_HEIGHT + HEADER_HEIGHT))
            # Content section (skip the gap)
            painter.drawLine(x_pos + 0.5, int(TITLE_HEIGHT + HEADER_HEIGHT + HEADER_GAP), x_pos + 0.5, canvas_height)
        
        painter.end()
