"""Core data type - a sediment core with image and calibration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .image import Image


@dataclass
class Core:
    """A sediment core sample.
    
    The anchor datatype for stratigraphy analysis. Holds the core image,
    calibration info, and layer boundaries.
    
    Attributes:
        name: Display name of the core
        image: The core photo
        mm_per_px: Calibration factor (physical mm per image pixel)
        layer_boundaries_px: Pixel depths where layers start/end
        parent: Optional parent reference (generic)
    """
    name: str
    image: Image
    mm_per_px: float = 0.5  # Default: 0.5mm per pixel
    layer_boundaries_px: list[int] = field(default_factory=list)
    parent: Any | None = None

    @property
    def height_px(self) -> int | None:
        """Height of the core image in pixels."""
        if self.image.shape is not None:
            return self.image.shape[0]
        return None

    @property
    def height_mm(self) -> float | None:
        """Height of the core in mm (from calibration)."""
        if self.height_px is not None:
            return self.height_px * self.mm_per_px
        return None

    @property
    def depth_range_mm(self) -> tuple[float, float] | None:
        """Depth range in mm (0 to height)."""
        if self.height_mm is not None:
            return (0.0, self.height_mm)
        return None

    def px_to_mm(self, px: int | float) -> float:
        """Convert pixel position to mm depth."""
        return px * self.mm_per_px

    def mm_to_px(self, mm: float) -> float:
        """Convert mm depth to pixel position."""
        return mm / self.mm_per_px

    def get_layer_boundaries_mm(self) -> list[float]:
        """Get layer boundaries in mm."""
        return [self.px_to_mm(px) for px in self.layer_boundaries_px]

    def set_layer_boundaries_mm(self, boundaries_mm: list[float]) -> None:
        """Set layer boundaries from mm values."""
        self.layer_boundaries_px = [int(self.mm_to_px(mm)) for mm in boundaries_mm]
