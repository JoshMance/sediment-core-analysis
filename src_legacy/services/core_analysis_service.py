"""CoreAnalysisService - manages CoreAnalysis operations."""
from __future__ import annotations

from models.entities import Core, CoreAnalysis
from models.datatypes import Layer
from models.services.colour_space_service import ColourSpaceService


class CoreAnalysisService:
    """Service for CoreAnalysis operations.
    
    Handles:
    - Creating new analyses
    - Layer operations
    - Recomputing summaries when layers change
    """

    @staticmethod
    def create_analysis(core: Core) -> CoreAnalysis:
        """Create a new CoreAnalysis for a Core.
        
        Args:
            core: The Core to analyze
            
        Returns:
            Empty CoreAnalysis ready for layer definition
        """
        return CoreAnalysis(core=core)

    @staticmethod
    def create_initial_layers(
        analysis: CoreAnalysis,
        boundary_depths_mm: list[float],
    ) -> None:
        """Create layers from a list of boundary depths.
        
        Args:
            analysis: The CoreAnalysis to populate
            boundary_depths_mm: Depths where layer boundaries occur
                               (must be sorted, first/last define extent)
        """
        if len(boundary_depths_mm) < 2:
            return
        
        analysis.layers.clear()
        
        # Sort and convert to pixels
        depths = sorted(boundary_depths_mm)
        pixels = [int(analysis.core.depth_to_px(d)) for d in depths]
        
        # Create layers between consecutive boundaries
        for i in range(len(pixels) - 1):
            analysis.add_layer(start_px=pixels[i], end_px=pixels[i + 1])

    @staticmethod
    def add_boundary_at_depth(analysis: CoreAnalysis, depth_mm: float) -> None:
        """Add a layer boundary at a given depth.
        
        Args:
            analysis: The CoreAnalysis
            depth_mm: Depth to add boundary
        """
        px = int(analysis.core.depth_to_px(depth_mm))
        analysis.add_boundary(px)

    @staticmethod
    def remove_boundary_at_depth(analysis: CoreAnalysis, depth_mm: float) -> None:
        """Remove a layer boundary at a given depth.
        
        Args:
            analysis: The CoreAnalysis
            depth_mm: Depth of boundary to remove
        """
        px = int(analysis.core.depth_to_px(depth_mm))
        analysis.remove_boundary(px)

    @staticmethod
    def move_boundary(analysis: CoreAnalysis, divider_idx: int, new_depth_mm: float) -> None:
        """Move a layer boundary to a new depth.
        
        Args:
            analysis: The CoreAnalysis
            divider_idx: Index of the divider (boundary between layer[i] and layer[i+1])
            new_depth_mm: New depth for the boundary
        """
        new_px = int(analysis.core.depth_to_px(new_depth_mm))
        analysis.move_boundary(divider_idx, new_px)

    @staticmethod
    def remove_boundary_at_index(analysis: CoreAnalysis, divider_idx: int) -> None:
        """Remove a layer boundary by divider index.
        
        Args:
            analysis: The CoreAnalysis
            divider_idx: Index of the divider (boundary between layer[i] and layer[i+1])
        """
        if divider_idx < 0 or divider_idx >= len(analysis.layers) - 1:
            return
        
        # Get the boundary pixel position
        boundary_px = analysis.layers[divider_idx].end_px
        analysis.remove_boundary(boundary_px)

    @staticmethod
    def get_layer_color(
        analysis: CoreAnalysis,
        layer: Layer,
    ) -> tuple[int, int, int]:
        """Get the mean RGB color for a layer.
        
        Args:
            analysis: The CoreAnalysis
            layer: The layer to get color for
            
        Returns:
            (R, G, B) tuple with values in [0, 255]
        """
        if analysis.core.derived.rgb is None:
            return (128, 128, 128)  # Gray fallback
        
        r, g, b = ColourSpaceService.mean_rgb_for_range(
            analysis.core.derived.rgb,
            layer.start_px,
            layer.end_px,
        )
        
        return (int(r * 255), int(g * 255), int(b * 255))
