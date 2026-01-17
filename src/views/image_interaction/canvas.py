from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt, QPoint

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        
        # Zoom and pan state
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        
        # Mouse tracking for panning
        self._is_panning = False
        self._last_mouse_pos = QPoint()
        
        # Enable mouse tracking
        self.setMouseTracking(True)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            # Apply pan and zoom transforms
            painter.translate(self._pan_x, self._pan_y)
            painter.scale(self._zoom, self._zoom)
            
            # Draw pixmap centered
            x = (self.width() / self._zoom - self._pixmap.width()) / 2
            y = (self.height() / self._zoom - self._pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), self._pixmap)

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel"""
        if not self._pixmap:
            return
        
        # Get mouse position for zoom anchor
        mouse_pos = event.position()
        
        # Calculate zoom factor
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        # Apply zoom limits
        new_zoom = self._zoom * zoom_factor
        if 0.1 <= new_zoom <= 10.0:
            # Zoom towards mouse position
            # Convert mouse pos to scene coords before zoom
            scene_x = (mouse_pos.x() - self._pan_x) / self._zoom
            scene_y = (mouse_pos.y() - self._pan_y) / self._zoom
            
            # Update zoom
            self._zoom = new_zoom
            
            # Adjust pan to keep mouse position fixed
            self._pan_x = mouse_pos.x() - scene_x * self._zoom
            self._pan_y = mouse_pos.y() - scene_y * self._zoom
            
            self.update()

    def mousePressEvent(self, event):
        """Start panning on middle or left button"""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._is_panning = True
            self._last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Pan the image while dragging"""
        if self._is_panning:
            delta = event.position().toPoint() - self._last_mouse_pos
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_mouse_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        """Stop panning"""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)

