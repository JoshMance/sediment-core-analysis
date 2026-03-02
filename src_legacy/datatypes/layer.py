"""Layer - a depth interval with categorical attributes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Layer:
    """A single layer/interval in a core analysis.
    
    Stores:
    - start_px, end_px: pixel boundaries of the interval
    - values: categorical attributes (keys defined by CoreAnalysis schema)
    
    The schema (what keys are valid, what values are allowed) is defined
    by the CoreAnalysis that owns this layer, not by the Layer itself.
    
    Attributes:
        start_px: Start pixel row (inclusive)
        end_px: End pixel row (exclusive)
        values: Dictionary of categorical attribute values
    """
    start_px: int
    end_px: int
    values: dict[str, Any] = field(default_factory=dict)

    @property
    def thickness_px(self) -> int:
        """Thickness in pixels."""
        return self.end_px - self.start_px

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the layer's attributes."""
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set an attribute value."""
        self.values[key] = value
