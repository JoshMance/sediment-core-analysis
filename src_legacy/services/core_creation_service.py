"""CoreCreationService - orchestrates Core entity creation."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image as PILImage

from models.datatypes import Image, ImageCalibration
from models.entities import Core, DerivedData
from models.services.colour_space_service import ColourSpaceService


class CoreCreationService:
    """Service for creating Core entities.
    
    Single entry point for Core creation, ensuring:
    - Image is loaded and normalized (vertical orientation)
    - Calibration is set
    - Derived data (RGB, Lab) is computed
    
    Note: Both create_from_file() and create_from_image() are actively used.
    create_from_file() is used by demos/controllers that load from disk.
    create_from_image() could be used when image data comes from other sources.
    """

    @staticmethod
    def create_from_file(
        file_path: Path | str,
        name: str | None = None,
        mm_per_px: float = 0.5,
    ) -> Core:
        """Create a Core from an image file.
        
        Args:
            file_path: Path to the core image
            name: Display name (defaults to filename stem)
            mm_per_px: Calibration factor
            
        Returns:
            Fully initialized Core with derived data
        """
        file_path = Path(file_path)
        name = name or file_path.stem
        
        # Load image
        pil_image = PILImage.open(file_path).convert("RGB")
        image_array = np.array(pil_image, dtype=np.uint8)
        
        # Auto-rotate if horizontal
        if image_array.shape[1] > image_array.shape[0]:
            image_array = np.rot90(image_array)
        
        image = Image(name=name, file_path=file_path, data=image_array)
        calibration = ImageCalibration(mm_per_px=mm_per_px)
        
        return CoreCreationService.create_from_image(image, calibration)

    @staticmethod
    def create_from_image(
        image: Image,
        calibration: ImageCalibration | None = None,
    ) -> Core:
        """Create a Core from an Image datatype.
        
        Args:
            image: The core image
            calibration: Calibration settings (defaults to 0.5 mm/px)
            
        Returns:
            Fully initialized Core with derived data
        """
        calibration = calibration or ImageCalibration()
        
        # Compute derived data
        derived = CoreCreationService._compute_derived(image)
        
        return Core(
            name=image.name,
            image=image,
            calibration=calibration,
            derived=derived,
        )

    @staticmethod
    def _compute_derived(image: Image) -> DerivedData:
        """Compute intrinsic derived data from image."""
        if image.data is None:
            return DerivedData()
        
        rgb_data = ColourSpaceService.compute_rgb_per_row(image.data)
        lab_data = ColourSpaceService.compute_lab_from_rgb(rgb_data)
        
        return DerivedData(rgb=rgb_data, lab=lab_data)

    @staticmethod
    def update_derived(core: Core) -> None:
        """Recompute derived data for an existing Core.
        
        Call this if the Core's image has changed.
        """
        core.derived = CoreCreationService._compute_derived(core.image)
