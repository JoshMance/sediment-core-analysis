"""CalibrationEntity — spatial calibration data for images."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalibrationEntity:
    """Spatial calibration linking pixel distance to real-world units.

    Attributes:
        id: Assigned by the Store on add().
        mm_per_px: Millimetres per pixel. 0.0 means uncalibrated.
    """
    id: str | None = None
    mm_per_px: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mm_per_px": self.mm_per_px,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CalibrationEntity":
        return cls(
            id=data["id"],
            mm_per_px=data.get("mm_per_px", 0.0),
        )
