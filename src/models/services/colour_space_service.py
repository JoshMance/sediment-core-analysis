"""ColourSpaceService - wraps science colour conversions."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from science import api
from models.datatypes import Data


class ColourSpaceService:
    """Service for colour space computations.
    
    Thin wrapper around science.api colour functions,
    adapting numpy arrays to/from Data datatypes.
    
    DESIGN QUESTION: Is this service necessary or overkill?
    
    Arguments FOR keeping it:
    - Single place for Data type adaptation logic
    - Clear responsibility: bridge between science (numpy) and models (Data)
    - Easy to extend later (caching, validation, color space management)
    - Keeps calling services simpler (they don't need numpy knowledge)
    
    Arguments AGAINST:
    - Thin indirection that just wraps science.api calls
    - Makes the call stack deeper
    - If Data is simple enough, services could handle adaptation directly
    
    CURRENT RECOMMENDATION: Keep it for now
    - Type adaptation is a legitimate concern to separate
    - Future extensions (caching, validation, multi-color-space support) would justify it
    - If we remove it, every service needing color data duplicates the adaptation logic
    
    Alternative: Remove this service, have CoreCreationService (and others) call
    science.api directly and create Data objects themselves.
    """

    @staticmethod
    def compute_rgb_per_row(image_array: NDArray[np.uint8]) -> Data:
        """Compute mean RGB per row from an image.
        
        Args:
            image_array: (H, W, 3) RGB image
            
        Returns:
            Data with (H, 3) RGB values in [0, 1]
        """
        rgb = api.mean_rgb_per_row(image_array)
        axis = np.arange(len(rgb), dtype=np.float64)
        return Data(name="RGB", values=rgb, axis=axis)

    @staticmethod
    def compute_lab_from_rgb(rgb_data: Data) -> Data:
        """Convert RGB data to CIELAB.
        
        Args:
            rgb_data: Data with (H, 3) RGB values
            
        Returns:
            Data with (H, 3) L*a*b* values
        """
        lab = api.rgb_to_lab(rgb_data.values)
        return Data(name="Lab", values=lab, axis=rgb_data.axis.copy())

    @staticmethod
    def mean_rgb_for_range(
        rgb_data: Data,
        start_px: int,
        end_px: int,
    ) -> tuple[float, float, float]:
        """Get mean RGB for a pixel range.
        
        Args:
            rgb_data: Data with (H, 3) RGB values
            start_px: Start row (inclusive)
            end_px: End row (exclusive)
            
        Returns:
            (R, G, B) tuple with values in [0, 1]
        """
        rgb = api.mean_rgb_for_range(rgb_data.values, start_px, end_px)
        return tuple(rgb)
