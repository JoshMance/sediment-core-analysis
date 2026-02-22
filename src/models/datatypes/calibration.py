"""ImageCalibration - mapping between pixels and physical units."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImageCalibration:
    """Linear scale calibration for converting between pixels and millimeters.
    
    This datatype represents ONLY the scale/ratio, not absolute position.
    It answers: "how many millimeters does one pixel represent?"
    
    Position information (e.g., "where does this image start in absolute depth")
    belongs in the Core entity or Layer entities, not here.
    
    Attributes:
        mm_per_px: Physical millimeters per pixel (scale ratio)
        calibrated: Whether this is an actual calibration vs. default placeholder
    
    Example:
        # Create from measurement: 100 pixels = 50 mm
        cal = ImageCalibration.from_measurement(px=100, mm=50)
        # Result: mm_per_px = 0.5, calibrated = True
    """
    mm_per_px: float = 0.5
    calibrated: bool = False
    
    @classmethod
    def from_measurement(cls, px: float, mm: float) -> ImageCalibration:
        """Create calibration from a measurement.
        
        Args:
            px: Number of pixels measured
            mm: Corresponding physical distance in millimeters
            
        Returns:
            ImageCalibration with computed ratio
            
        Raises:
            ValueError: If px is zero or negative
        """
        if px <= 0:
            raise ValueError(f"Pixel measurement must be positive, got {px}")
        if mm <= 0:
            raise ValueError(f"Physical measurement must be positive, got {mm}")
        
        return cls(mm_per_px=mm / px, calibrated=True)

    def px_to_mm(self, px: int | float) -> float:
        """Convert pixel distance to millimeters.
        
        Args:
            px: Distance in pixels
            
        Returns:
            Distance in millimeters
        """
        return px * self.mm_per_px

    def mm_to_px(self, mm: float) -> float:
        """Convert millimeter distance to pixels.
        
        Args:
            mm: Distance in millimeters
            
        Returns:
            Distance in pixels
        """
        return mm / self.mm_per_px
