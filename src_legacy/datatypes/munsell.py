"""Munsell colour notation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Munsell:
    """Munsell colour specification.
    
    Represents a colour in the Munsell system (hue, value, chroma).
    
    Expected valid ranges (not enforced by this datatype):
    - Hue: One of the Munsell hue designations (e.g., "5YR", "10R", "2.5Y")
      Valid hues follow the pattern: [value][color] where color is R, YR, Y, GY, G, BG, B, PB, P, RP
      and value is typically 2.5, 5, 7.5, or 10. Neutral grays use "N".
    - Value: 0 (ideal black) to 10 (ideal white), typically 2-8 for soil samples
    - Chroma: 0 (neutral/gray) upward, typically 1-8 for soils, can go higher
      (maximum chroma depends on specific hue and value)
    
    Validation should occur at input boundaries (user entry, file loading),
    not in this datatype, to avoid performance overhead on every instantiation.
    
    Attributes:
        hue: Hue string (e.g., "5YR", "10R", "2.5Y", "N" for neutral)
        value: Value/lightness, typically 0-10
        chroma: Chroma/saturation, typically 0-8+ (depends on hue/value)
    """
    hue: str
    value: float
    chroma: float

    def __str__(self) -> str:
        """Return standard Munsell notation (e.g., '5YR 4/2')."""
        return f"{self.hue} {self.value:.0f}/{self.chroma:.0f}"

    @classmethod
    def from_string(cls, notation: str) -> "Munsell":
        """Parse Munsell notation string (e.g., '5YR 4/2').
        
        Args:
            notation: String in format 'HUE VALUE/CHROMA'
            
        Returns:
            Munsell instance
            
        Raises:
            ValueError: If notation cannot be parsed
        """
        parts = notation.strip().split()
        if len(parts) != 2:
            raise ValueError(f"Invalid Munsell notation: {notation}")
        
        hue = parts[0]
        value_chroma = parts[1].split("/")
        if len(value_chroma) != 2:
            raise ValueError(f"Invalid value/chroma: {parts[1]}")
        
        return cls(
            hue=hue,
            value=float(value_chroma[0]),
            chroma=float(value_chroma[1]),
        )
