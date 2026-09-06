"""Domain records for Core Studio divisions and layer intervals."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoreDivision:
    """An interior boundary on a core's oriented image-depth axis."""

    id: str
    position_px: int

    def to_dict(self) -> dict:
        return {"id": self.id, "position_px": self.position_px}

    @classmethod
    def from_dict(cls, data: dict) -> "CoreDivision":
        return cls(id=data["id"], position_px=int(data["position_px"]))


@dataclass
class CoreLayer:
    """A named interval between two divisions, or an image edge and division."""

    id: str
    start_division_id: str | None
    end_division_id: str | None
    title: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_division_id": self.start_division_id,
            "end_division_id": self.end_division_id,
            "title": self.title,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoreLayer":
        return cls(
            id=data["id"],
            start_division_id=data.get("start_division_id"),
            end_division_id=data.get("end_division_id"),
            title=data.get("title", ""),
            note=data.get("note", ""),
        )