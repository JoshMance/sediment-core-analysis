from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPaintEvent, QWheelEvent, QMouseEvent, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal

# Zoom constants
ZOOM_MIN = 0.1
ZOOM_MAX = 10.0
ZOOM_FACTOR = 1.1

# Mode constants
MODE_PAN = 'pan'
MODE_SELECT = 'select'
MODE_CALIBRATE = 'calibrate'

# Interaction constants
HANDLE_SIZE = 8
HIT_TOLERANCE = 10

class ImageCanvas(QWidget):
    """Canvas widget for displaying and interacting with images (pan and zoom)."""
    
    # Signals
    selection_changed = Signal(object)  # Emits QRectF in image coordinates
    calibration_changed = Signal(object, object)  # Emits (QPointF, QPointF) in image coords
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = None
        
        # Zoom and pan state
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        
        # Interaction mode
        self._mode = MODE_PAN
        
        # Selection state (stored in image coordinates)
        self._selection_rect: QRectF | None = None
        self._selection_visible = False
        self._dragging_selection = None  # 'move', 'resize_tl', 'resize_br', etc.
        self._drag_start_pos = QPoint()
        self._drag_start_rect = QRectF()
        
        # Calibration state (stored in image coordinates)
        self._calib_point1: QPointF | None = None
        self._calib_point2: QPointF | None = None
        self._calib_visible = False
        self._dragging_calib = None  # 'point1', 'point2'
        
        # Mouse tracking for panning
        self._is_panning = False
        self._last_mouse_pos = QPoint()
        
        # Enable mouse tracking
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the pixmap to display and reset view transforms."""
        self._pixmap = pixmap
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self.update()

    def set_mode(self, mode: str) -> None:
        """Set interaction mode (pan, select, calibrate)."""
        self._mode = mode
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def set_selection_visible(self, visible: bool) -> None:
        """Show or hide the selection rectangle."""
        self._selection_visible = visible
        if visible and self._selection_rect is None and self._pixmap:
            # Initialize selection rect in center of image
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()
            w, h = img_w * 0.5, img_h * 0.5
            self._selection_rect = QRectF(img_w * 0.25, img_h * 0.25, w, h)
        self.update()

    def set_calibration_visible(self, visible: bool) -> None:
        """Show or hide the calibration line."""
        self._calib_visible = visible
        if visible and self._calib_point1 is None and self._pixmap:
            # Initialize calibration line in center of image
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()
            self._calib_point1 = QPointF(img_w * 0.3, img_h * 0.5)
            self._calib_point2 = QPointF(img_w * 0.7, img_h * 0.5)
        self.update()

    def get_selection_rect(self) -> QRectF | None:
        """Get selection rectangle in image coordinates."""
        return self._selection_rect

    def get_selection_pixmap(self) -> QPixmap | None:
        """Extract the selected region as a pixmap."""
        if not self._pixmap or not self._selection_rect:
            return None
        rect = self._selection_rect.toRect()
        return self._pixmap.copy(rect)

    def get_calibration_points(self) -> tuple[QPointF, QPointF] | None:
        """Get calibration points in image coordinates."""
        if self._calib_point1 and self._calib_point2:
            return (self._calib_point1, self._calib_point2)
        return None

    def get_calibration_pixel_distance(self) -> float:
        """Get the distance between calibration points in image pixels."""
        if not self._calib_point1 or not self._calib_point2:
            return 0.0
        dx = self._calib_point2.x() - self._calib_point1.x()
        dy = self._calib_point2.y() - self._calib_point1.y()
        return (dx * dx + dy * dy) ** 0.5

    def zoom_in(self) -> None:
        """Zoom in, centered on viewport."""
        self._apply_zoom(ZOOM_FACTOR, center_on_viewport=True)

    def zoom_out(self) -> None:
        """Zoom out, centered on viewport."""
        self._apply_zoom(1.0 / ZOOM_FACTOR, center_on_viewport=True)

    def _apply_zoom(self, zoom_factor: float, center_on_viewport: bool = False, anchor_pos: QPoint | None = None) -> None:
        """Apply zoom with optional anchoring to a specific point or viewport center."""
        if not self._pixmap:
            return

        new_zoom = self._zoom * zoom_factor
        if not (ZOOM_MIN <= new_zoom <= ZOOM_MAX):
            return

        if center_on_viewport:
            # Zoom centered on viewport
            center_x = self.width() / 2
            center_y = self.height() / 2
            scene_x = (center_x - self._pan_x) / self._zoom
            scene_y = (center_y - self._pan_y) / self._zoom
            self._zoom = new_zoom
            self._pan_x = center_x - scene_x * self._zoom
            self._pan_y = center_y - scene_y * self._zoom
        elif anchor_pos:
            # Zoom anchored at specific position
            scene_x = (anchor_pos.x() - self._pan_x) / self._zoom
            scene_y = (anchor_pos.y() - self._pan_y) / self._zoom
            self._zoom = new_zoom
            self._pan_x = anchor_pos.x() - scene_x * self._zoom
            self._pan_y = anchor_pos.y() - scene_y * self._zoom
        else:
            # Simple zoom without repositioning
            self._zoom = new_zoom

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the image with current pan and zoom transforms."""
        super().paintEvent(event)
        if self._pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Apply pan and zoom transforms
            painter.translate(self._pan_x, self._pan_y)
            painter.scale(self._zoom, self._zoom)
            
            # Draw pixmap centered in viewport
            img_x = (self.width() / self._zoom - self._pixmap.width()) / 2
            img_y = (self.height() / self._zoom - self._pixmap.height()) / 2
            painter.drawPixmap(int(img_x), int(img_y), self._pixmap)
            
            # Draw overlays (also in image coordinate space)
            painter.translate(img_x, img_y)
            
            if self._selection_visible and self._selection_rect:
                self._draw_selection(painter)
            
            if self._calib_visible and self._calib_point1 and self._calib_point2:
                self._draw_calibration(painter)

    def _draw_selection(self, painter: QPainter) -> None:
        """Draw selection rectangle with resize handles."""
        # Draw dimmed overlay outside selection
        if self._pixmap:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 180))  # 70% opacity black
            
            # Create a path with the full image and cut out the selection
            from PySide6.QtGui import QPainterPath
            full_path = QPainterPath()
            full_path.addRect(0, 0, self._pixmap.width(), self._pixmap.height())
            selection_path = QPainterPath()
            selection_path.addRect(self._selection_rect)
            overlay_path = full_path.subtracted(selection_path)
            painter.drawPath(overlay_path)
            painter.restore()
        
        # Draw selection border
        pen = QPen(QColor(0, 120, 215), 2 / self._zoom)  # Blue border
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._selection_rect)
        
        # Draw resize handles at corners and edges
        handle_size = HANDLE_SIZE / self._zoom
        handles = self._get_selection_handles()
        painter.setBrush(QColor(0, 120, 215))
        for handle_rect in handles.values():
            painter.drawRect(handle_rect)

    def _draw_calibration(self, painter: QPainter) -> None:
        """Draw calibration line with endpoint handles."""
        pen = QPen(QColor(255, 0, 0), 2 / self._zoom)  # Red line
        painter.setPen(pen)
        painter.drawLine(self._calib_point1, self._calib_point2)
        
        # Draw perpendicular end caps
        cap_len = 10 / self._zoom
        dx = self._calib_point2.x() - self._calib_point1.x()
        dy = self._calib_point2.y() - self._calib_point1.y()
        length = (dx * dx + dy * dy) ** 0.5
        if length > 0:
            perp_x = -dy / length * cap_len
            perp_y = dx / length * cap_len
            # End cap at point 1
            painter.drawLine(
                QPointF(self._calib_point1.x() - perp_x, self._calib_point1.y() - perp_y),
                QPointF(self._calib_point1.x() + perp_x, self._calib_point1.y() + perp_y)
            )
            # End cap at point 2
            painter.drawLine(
                QPointF(self._calib_point2.x() - perp_x, self._calib_point2.y() - perp_y),
                QPointF(self._calib_point2.x() + perp_x, self._calib_point2.y() + perp_y)
            )
        
        # Draw draggable endpoint circles
        handle_size = HANDLE_SIZE / self._zoom
        painter.setBrush(QColor(255, 0, 0))
        painter.drawEllipse(self._calib_point1, handle_size / 2, handle_size / 2)
        painter.drawEllipse(self._calib_point2, handle_size / 2, handle_size / 2)

    def _widget_to_image(self, widget_pos: QPoint) -> QPointF:
        """Convert widget coordinates to image coordinates."""
        if not self._pixmap:
            return QPointF()
        img_x = (self.width() / self._zoom - self._pixmap.width()) / 2
        img_y = (self.height() / self._zoom - self._pixmap.height()) / 2
        image_x = (widget_pos.x() - self._pan_x) / self._zoom - img_x
        image_y = (widget_pos.y() - self._pan_y) / self._zoom - img_y
        return QPointF(image_x, image_y)

    def _get_selection_handles(self) -> dict[str, QRectF]:
        """Get resize handle rectangles for selection (in image coordinates)."""
        if not self._selection_rect:
            return {}
        
        hs = HANDLE_SIZE / self._zoom
        r = self._selection_rect
        return {
            'tl': QRectF(r.left() - hs/2, r.top() - hs/2, hs, hs),
            'tr': QRectF(r.right() - hs/2, r.top() - hs/2, hs, hs),
            'bl': QRectF(r.left() - hs/2, r.bottom() - hs/2, hs, hs),
            'br': QRectF(r.right() - hs/2, r.bottom() - hs/2, hs, hs),
            't': QRectF(r.center().x() - hs/2, r.top() - hs/2, hs, hs),
            'b': QRectF(r.center().x() - hs/2, r.bottom() - hs/2, hs, hs),
            'l': QRectF(r.left() - hs/2, r.center().y() - hs/2, hs, hs),
            'r': QRectF(r.right() - hs/2, r.center().y() - hs/2, hs, hs),
        }

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in/out with mouse wheel, anchored at cursor position."""
        delta = event.angleDelta().y()
        zoom_factor = ZOOM_FACTOR if delta > 0 else (1.0 / ZOOM_FACTOR)
        anchor_pos = event.position().toPoint()
        self._apply_zoom(zoom_factor, anchor_pos=anchor_pos)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for overlay interaction or panning."""
        # Middle mouse button always pans
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            return
        
        if event.button() != Qt.LeftButton:
            return
        
        img_pos = self._widget_to_image(event.position().toPoint())
        
        # Handle selection mode
        if self._mode == MODE_SELECT and self._selection_visible and self._selection_rect:
            # Check if clicking on a resize handle
            handles = self._get_selection_handles()
            for handle_name, handle_rect in handles.items():
                if handle_rect.contains(img_pos):
                    self._dragging_selection = f'resize_{handle_name}'
                    self._drag_start_pos = event.position().toPoint()
                    self._drag_start_rect = QRectF(self._selection_rect)
                    return
            
            # Check if clicking inside selection to move it
            if self._selection_rect.contains(img_pos):
                self._dragging_selection = 'move'
                self._drag_start_pos = event.position().toPoint()
                self._drag_start_rect = QRectF(self._selection_rect)
                return
        
        # Handle calibration mode
        if self._mode == MODE_CALIBRATE and self._calib_visible:
            tolerance = HIT_TOLERANCE / self._zoom
            if self._calib_point1:
                dx1 = img_pos.x() - self._calib_point1.x()
                dy1 = img_pos.y() - self._calib_point1.y()
                if (dx1 * dx1 + dy1 * dy1) < tolerance * tolerance:
                    self._dragging_calib = 'point1'
                    return
            
            if self._calib_point2:
                dx2 = img_pos.x() - self._calib_point2.x()
                dy2 = img_pos.y() - self._calib_point2.y()
                if (dx2 * dx2 + dy2 * dy2) < tolerance * tolerance:
                    self._dragging_calib = 'point2'
                    return
        
        # If we get here, didn't hit any overlay - allow panning
        self._is_panning = True
        self._last_mouse_pos = event.position().toPoint()
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Pan the image while dragging."""
        # Handle selection dragging
        if self._dragging_selection and self._selection_rect:
            img_pos = self._widget_to_image(event.position().toPoint())
            delta_widget = event.position().toPoint() - self._drag_start_pos
            delta_img = QPointF(delta_widget.x() / self._zoom, delta_widget.y() / self._zoom)
            
            if self._dragging_selection == 'move':
                # Move entire rectangle
                self._selection_rect.moveTo(
                    self._drag_start_rect.x() + delta_img.x(),
                    self._drag_start_rect.y() + delta_img.y()
                )
            else:
                # Resize from handle
                self._resize_selection(self._dragging_selection, img_pos)
            
            self.selection_changed.emit(self._selection_rect)
            self.update()
            return
        
        # Handle calibration dragging
        if self._dragging_calib:
            img_pos = self._widget_to_image(event.position().toPoint())
            if self._dragging_calib == 'point1':
                self._calib_point1 = img_pos
            elif self._dragging_calib == 'point2':
                self._calib_point2 = img_pos
            self.calibration_changed.emit(self._calib_point1, self._calib_point2)
            self.update()
            return
        
        # Handle panning
        if self._is_panning:
            delta = event.position().toPoint() - self._last_mouse_pos
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_mouse_pos = event.position().toPoint()
            self.update()
            return
        
        # Update cursor based on hover
        self._update_cursor(event.position().toPoint())

    def _resize_selection(self, handle: str, img_pos: QPointF) -> None:
        """Resize selection rectangle from a specific handle."""
        rect = self._selection_rect
        
        if 't' in handle:
            rect.setTop(img_pos.y())
        if 'b' in handle:
            rect.setBottom(img_pos.y())
        if 'l' in handle:
            rect.setLeft(img_pos.x())
        if 'r' in handle:
            rect.setRight(img_pos.x())
        
        # Ensure minimum size
        if rect.width() < 10:
            if 'l' in handle:
                rect.setLeft(rect.right() - 10)
            else:
                rect.setRight(rect.left() + 10)
        if rect.height() < 10:
            if 't' in handle:
                rect.setTop(rect.bottom() - 10)
            else:
                rect.setBottom(rect.top() + 10)
        
        self._selection_rect = rect.normalized()

    def _update_cursor(self, widget_pos: QPoint) -> None:
        """Update cursor based on what's under the mouse."""
        if self._mode == MODE_SELECT and self._selection_visible and self._selection_rect:
            img_pos = self._widget_to_image(widget_pos)
            handles = self._get_selection_handles()
            
            for handle_name, handle_rect in handles.items():
                if handle_rect.contains(img_pos):
                    # Set appropriate resize cursor
                    if handle_name in ('tl', 'br'):
                        self.setCursor(Qt.SizeFDiagCursor)
                    elif handle_name in ('tr', 'bl'):
                        self.setCursor(Qt.SizeBDiagCursor)
                    elif handle_name in ('t', 'b'):
                        self.setCursor(Qt.SizeVerCursor)
                    elif handle_name in ('l', 'r'):
                        self.setCursor(Qt.SizeHorCursor)
                    return
            
            if self._selection_rect.contains(img_pos):
                self.setCursor(Qt.SizeAllCursor)
                return
        
        if self._mode == MODE_CALIBRATE and self._calib_visible:
            img_pos = self._widget_to_image(widget_pos)
            tolerance = HIT_TOLERANCE / self._zoom
            
            for point in [self._calib_point1, self._calib_point2]:
                if point:
                    dx = img_pos.x() - point.x()
                    dy = img_pos.y() - point.y()
                    if (dx * dx + dy * dy) < tolerance * tolerance:
                        self.setCursor(Qt.CrossCursor)
                        return
        
        self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on mouse button release."""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._is_panning = False
            self._dragging_selection = None
            self._dragging_calib = None
            self.setCursor(Qt.ArrowCursor)

