"""Core entity - a sediment core with intrinsic derived data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from models.datatypes import Image, ImageCalibration, Data

if TYPE_CHECKING:
    from numpy.typing import NDArray
    import numpy as np


@dataclass
class DerivedData:
    """Intrinsic derived data computed from the core image.
    
    These are deterministic computations from the image - 
    they don't depend on user interpretation.
    
    DESIGN QUESTION: Is this dataclass necessary or overengineered?
    
    Current approach:
        DerivedData(rgb: Data | None, lab: Data | None)
        
    Alternative 1 - Individual fields on Core:
        Core.rgb: Data | None
        Core.lab: Data | None
        Pro: Flatter, simpler
        Con: Mixes derived and intrinsic data on Core
        
    Alternative 2 - Dictionary (RECOMMENDED):
        Core.derived: dict[str, Data]
        Pro: Flexible, supports discovery (core.derived.keys()), no schema changes for new data
        Con: No type hints for specific fields, typo-prone
        Benefits: Aligns with data-driven view architecture! Views can discover what
                  derived data exists without hardcoding field names.
    
    TODO: Consider refactoring to dict approach when implementing data-driven
    stratigraphy panel column discovery.
    
    Attributes:
        rgb: Mean RGB per row - Data with shape (H, 3), values in [0, 1]
        lab: CIELAB per row - Data with shape (H, 3), L* in [0,100], a*/b* in [-128, 127]
    """
    rgb: Data | None = None
    lab: Data | None = None


@dataclass
class Core:
    """A sediment core sample.
    
    The Core entity holds:
    - Image reference + calibration (intrinsic properties)
    - Deterministic derived measurements (rgb, lab profiles)
    
    Layer boundaries and interpretations belong to CoreAnalysis, not Core.
    
    The core's depth system: pixel 0 of the image corresponds to depth 0 mm.
    The calibration provides the scale (mm per pixel), and this entity manages
    the absolute position.
    
    Attributes:
        id: Unique identifier
        name: Display name
        image: The core image
        calibration: Pixel-to-millimeter scale mapping
        derived: Computed intrinsic data (rgb, lab profiles)
        top_depth_mm: Absolute depth at pixel 0 (typically 0.0)
    """
    name: str
    image: Image
    calibration: ImageCalibration = field(default_factory=ImageCalibration)
    derived: DerivedData = field(default_factory=DerivedData)
    top_depth_mm: float = 0.0
    id: UUID = field(default_factory=uuid4)

    @property
    def height_px(self) -> int | None:
        """Height of the core image in pixels."""
        if self.image.shape is not None:
            return self.image.shape[0]
        return None
    
    @property
    def width_px(self) -> int | None:
        """Width of the core image in pixels."""
        if self.image.shape is not None:
            return self.image.shape[1]
        return None
    
    @property
    def height_mm(self) -> float | None:
        """Height of the core image in millimeters."""
        if self.height_px is not None:
            return self.calibration.px_to_mm(self.height_px)
        return None
    
    @property
    def width_mm(self) -> float | None:
        """Width of the core image in millimeters."""
        if self.width_px is not None:
            return self.calibration.px_to_mm(self.width_px)
        return None

    @property
    def depth_range_mm(self) -> tuple[float, float] | None:
        """Absolute depth range in mm."""
        if self.height_mm is not None:
            return (self.top_depth_mm, self.top_depth_mm + self.height_mm)
        return None

    def px_to_depth(self, px: int | float) -> float:
        """Convert pixel row to absolute depth in mm.
        
        Args:
            px: Pixel row (0 = top of image)
            
        Returns:
            Absolute depth in millimeters
        """
        return self.top_depth_mm + self.calibration.px_to_mm(px)

    def depth_to_px(self, depth_mm: float) -> float:
        """Convert absolute depth in mm to pixel row.
        
        Args:
            depth_mm: Absolute depth in millimeters
            
        Returns:
            Pixel row (may be fractional)
        """
        return self.calibration.mm_to_px(depth_mm - self.top_depth_mm)
