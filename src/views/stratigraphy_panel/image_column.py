from PySide6.QtGui import QPainter, QPixmap, QPen, QTransform
from PySide6.QtCore import QRectF, Qt
from .column import Column

class ImageColumn(Column):
    """Column that displays an image (e.g., sediment core photo)."""
    
    def __init__(self, title: str, pixmap: QPixmap | None = None, width: int = 200) -> None:
        super().__init__(title, width)
        self.pixmap = self._ensure_vertical_orientation(pixmap) if pixmap else None
    
    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Set the image to display."""
        self.pixmap = self._ensure_vertical_orientation(pixmap)
    
    def _ensure_vertical_orientation(self, pixmap: QPixmap) -> QPixmap:
        """Rotate image 90° if width > height to make longest side vertical."""
        if not pixmap or pixmap.isNull():
            return pixmap
        
        # If width > height, rotate 90 degrees
        if pixmap.width() > pixmap.height():
            transform = QTransform()
            transform.rotate(90)
            return pixmap.transformed(transform, Qt.SmoothTransformation)
        
        return pixmap
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """Calculate the height needed to display image at correct aspect ratio."""
        if not self.pixmap or self.pixmap.isNull():
            return 0.0
        
        # Calculate height needed to maintain aspect ratio at given width
        aspect_ratio = self.pixmap.height() / self.pixmap.width()
        return width * aspect_ratio
    
    def _paint_content(self, painter: QPainter, rect: QRectF, depth_range: tuple[float, float]) -> None:
        """Paint the image maintaining aspect ratio."""
        if not self.pixmap or self.pixmap.isNull():
            return
        
        # Scale to column width, maintain aspect ratio
        aspect_ratio = self.pixmap.height() / self.pixmap.width()
        scaled_height = rect.width() * aspect_ratio
        
        # Create rect for scaled image starting at top of content area
        image_rect = QRectF(rect.x(), rect.y(), rect.width(), scaled_height)
        
        # Draw the image
        painter.drawPixmap(image_rect.toRect(), self.pixmap)
