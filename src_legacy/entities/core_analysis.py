"""CoreAnalysis entity - interpretation layer over a Core."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from models.datatypes import Layer, Data
from models.entities.core import Core


@dataclass
class LayerSchema:
    """Schema defining valid categorical attributes for layers.
    
    Attributes:
        fields: Dict mapping field name to allowed values (list) or type hint
                e.g., {"lithology": ["sand", "silt", "clay"], "description": str}
    """
    fields: dict[str, list[str] | type] = field(default_factory=dict)

    def validate_layer(self, layer: Layer) -> list[str]:
        """Validate a layer's values against the schema.
        
        Returns list of validation error messages (empty if valid).
        """
        errors = []
        for key, value in layer.values.items():
            if key not in self.fields:
                errors.append(f"Unknown field: {key}")
            elif isinstance(self.fields[key], list):
                if value not in self.fields[key]:
                    errors.append(f"Invalid value for {key}: {value}")
        return errors


@dataclass
class CoreAnalysis:
    """Analysis/interpretation of a Core.
    
    CoreAnalysis owns:
    - Layer segmentation (boundaries and categorical attributes)
    - Schema defining valid layer attributes
    - Interpretation-derived statistics
    
    CoreAnalysis does NOT own continuous data - it references
    the Core's derived data. For layer-level statistics (e.g., mean RGB
    for a layer), use service methods that delegate to the science layer.
    
    Design consideration: Currently holds a reference to the full Core object.
    For serialization/persistence, consider whether to store core_id: UUID instead
    and resolve the reference separately.
    
    Attributes:
        id: Unique identifier
        core: The Core being analyzed (TODO: consider core_id: UUID for serialization)
        layers: Ordered list of layers (from top to bottom)
        schema: Definition of valid layer attributes
    """
    core: Core
    layers: list[Layer] = field(default_factory=list)
    schema: LayerSchema = field(default_factory=LayerSchema)
    id: UUID = field(default_factory=uuid4)

    def add_layer(self, start_px: int, end_px: int, values: dict[str, Any] | None = None) -> Layer:
        """Add a new layer to the analysis.
        
        Args:
            start_px: Start pixel (inclusive)
            end_px: End pixel (exclusive)
            values: Initial categorical values
            
        Returns:
            The created Layer
        """
        layer = Layer(start_px=start_px, end_px=end_px, values=values or {})
        self.layers.append(layer)
        self._sort_layers()
        return layer

    def add_boundary(self, px: int) -> None:
        """Add a boundary at the given pixel, splitting any existing layer."""
        # Find which layer contains this pixel
        for i, layer in enumerate(self.layers):
            if layer.start_px <= px < layer.end_px:
                # Split this layer
                new_layer = Layer(
                    start_px=px,
                    end_px=layer.end_px,
                    values=dict(layer.values),  # Copy values
                )
                layer.end_px = px
                self.layers.insert(i + 1, new_layer)
                return
        
        # If no existing layer, this might be extending coverage
        # For now, do nothing - layers must be explicitly created

    def remove_boundary(self, px: int) -> None:
        """Remove a boundary, merging adjacent layers."""
        for i, layer in enumerate(self.layers[:-1]):
            if layer.end_px == px:
                # Merge with next layer
                next_layer = self.layers[i + 1]
                layer.end_px = next_layer.end_px
                # Keep this layer's values (could merge somehow)
                self.layers.pop(i + 1)
                return

    def move_boundary(self, divider_idx: int, new_px: int) -> None:
        """Move a boundary between two layers to a new position.
        
        Args:
            divider_idx: Index of the divider (boundary between layer[i] and layer[i+1])
            new_px: New pixel position for the boundary
        """
        if divider_idx < 0 or divider_idx >= len(self.layers) - 1:
            return
        
        layer = self.layers[divider_idx]
        next_layer = self.layers[divider_idx + 1]
        
        # Clamp to valid range (don't collapse layers to zero width)
        new_px = max(layer.start_px + 1, min(new_px, next_layer.end_px - 1))
        
        layer.end_px = new_px
        next_layer.start_px = new_px

    def _sort_layers(self) -> None:
        """Keep layers sorted by start_px."""
        self.layers.sort(key=lambda l: l.start_px)

    def layer_at_px(self, px: int) -> Layer | None:
        """Get the layer containing a given pixel."""
        for layer in self.layers:
            if layer.start_px <= px < layer.end_px:
                return layer
        return None

    def layer_at_depth(self, depth_mm: float) -> Layer | None:
        """Get the layer at a given depth."""
        px = int(self.core.depth_to_px(depth_mm))
        return self.layer_at_px(px)
