"""Image column for displaying sediment core photos."""

from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtCore import QRectF, Qt
from .base import BaseColumn
from ..rows import StratRow


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
        
        Args:
            pixmap: Image to display
        """
        self._pixmap = self._ensure_vertical_orientation(pixmap)
    
    def get_pixmap(self) -> QPixmap | None:
        """Get the current pixmap."""
        return self._pixmap
    
    def set_depth_range(self, min_depth: float, max_depth: float) -> None:
        """
        Set the physical depth range this image represents.
        
        Args:
            min_depth: Minimum depth (e.g., 0.0 cm)
            max_depth: Maximum depth (e.g., 100.0 cm)
        """
        self._depth_range = (min_depth, max_depth)
    
    def set_calibration(self, mm_per_pixel: float, offset_mm: float = 0.0) -> None:
        """
        Set scale factor from image pixels to real-world depth.
        
        This is the primary way to calibrate an image when you know the physical
        scale (e.g., from a scale bar or metadata).
        
        Args:
            mm_per_pixel: Physical depth per image pixel (e.g., 0.5 = each pixel is 0.5mm)
            offset_mm: Starting depth in mm (default 0.0 means image starts at 0mm depth)
        """
        if not self._pixmap:
            return
        
        image_height_px = self._pixmap.height()
        total_depth_mm = image_height_px * mm_per_pixel
        self.set_depth_range(offset_mm, offset_mm + total_depth_mm)
    
    def apply_default_calibration(self) -> None:
        """
        Apply a sensible default calibration if no depth range is set.
        
        Default: 0.5 mm/pixel (typical for sediment core scans)
        This makes a 1000px image represent 50cm of depth.
        """
        if self._depth_range is None and self._pixmap:
            self.set_calibration(mm_per_pixel=0.5)
    
    def provides_scale(self) -> bool:
        """This column defines scale if it has both image and depth range."""
        return self._defines_scale and self._pixmap is not None and self._depth_range is not None
    
    def get_scale(self, width: float) -> tuple[float, tuple[float, float]] | None:
        """
        Get the canonical scale: pixel height and physical depth range.
        
        Args:
            width: Actual pixel width allocated to this column
            
        Returns:
            (pixel_height, (min_depth, max_depth)) or None if no scale defined
        """
        if not self.provides_scale():
            return None
        
        # Calculate pixel height from aspect ratio
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        pixel_height = width * aspect_ratio
        
        return (pixel_height, self._depth_range)
    
    def _ensure_vertical_orientation(self, pixmap: QPixmap) -> QPixmap:
        """
        Rotate image 90° if width > height to make longest side vertical.
        
        Args:
            pixmap: Input image
            
        Returns:
            Oriented image (original or rotated)
        """
        if not pixmap or pixmap.isNull():
            return pixmap
        
        # If width > height, rotate 90 degrees
        if pixmap.width() > pixmap.height():
            transform = QTransform()
            transform.rotate(90)
            return pixmap.transformed(transform, Qt.SmoothTransformation)
        
        return pixmap
    
    def get_content_height(self, width: float, depth_range: tuple[float, float]) -> float:
        """
        Calculate height based on aspect ratio.
        
        If this column provides scale, its natural height becomes canonical.
        Otherwise, it stretches/compresses to match the provided depth_range scale.
        
        Args:
            width: Actual pixel width allocated to this column
            depth_range: External depth range (if this column doesn't define scale)
            
        Returns:
            Height in pixels
        """
        if not self._pixmap or self._pixmap.isNull():
            return 0.0
        
        # Natural height from aspect ratio
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        natural_height = width * aspect_ratio
        
        # If we provide scale, use natural height
        if self.provides_scale():
            return natural_height
        
        # Otherwise, if external depth_range provided and we have our own range,
        # scale proportionally
        if self._depth_range and depth_range:
            our_depth_span = self._depth_range[1] - self._depth_range[0]
            external_depth_span = depth_range[1] - depth_range[0]
            if external_depth_span > 0:
                scale_factor = our_depth_span / external_depth_span
                return natural_height * scale_factor
        
        return natural_height
    
    def _paint_content(self, painter, rect: QRectF, depth_range: tuple[float, float], rows: list[StratRow]) -> None:
        """
        Paint the image maintaining aspect ratio, with dividers overlay.
        
        Args:
            painter: QPainter to draw with
            rect: Content area rectangle (already adjusted for scroll offset)
            depth_range: Depth range for positioning
            rows: List of depth intervals (draws dividers between them)
        """
        if not self._pixmap or self._pixmap.isNull():
            return
        
        # Scale to column width, maintain aspect ratio
        aspect_ratio = self._pixmap.height() / self._pixmap.width()
        scaled_height = rect.width() * aspect_ratio
        
        # Create rect for scaled image starting at top of content area
        image_rect = QRectF(rect.x(), rect.y(), rect.width(), scaled_height)
        
        # Draw the image
        painter.drawPixmap(image_rect.toRect(), self._pixmap)
    
    @property
    def has_data(self) -> bool:
        """Whether this column contains valid image data."""
        return self._pixmap is not None and not self._pixmap.isNull()
