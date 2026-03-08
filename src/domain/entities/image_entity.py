"""Image entity for the variables panel."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass
class ImageEntity:
    """An image entity.
    
    Attributes:
        id: Unique identifier (assigned by Store)
        name: Display name of the image
        file_path: Path to the image file (or None if not saved)
        data: The image data as an (h, w, 3) numpy array (RGB)
    """
    name: str
    id: str | None = None
    file_path: Path | None = None
    data: NDArray[np.uint8] | None = field(default=None, repr=False)

    @property
    def shape(self) -> tuple[int, int, int] | None:
        """Return the shape of the image data (height, width, channels)."""
        if self.data is not None:
            return self.data.shape
        return None

    def to_dict(self) -> dict:
        """Serialise to a plain dict for session.json.

        Pixel data is NOT included — the archive service owns writing the
        asset file and will rewrite 'file_path' to the bundled asset path.
        """
        return {
            "id": self.id,
            "name": self.name,
            "file_path": str(self.file_path) if self.file_path is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageEntity":
        """Reconstruct from a plain dict. Pixel data is not restored here —
        the AppController reloads it from the resolved asset path."""
        file_path = Path(data["file_path"]) if data.get("file_path") else None
        return cls(
            id=data["id"],
            name=data["name"],
            file_path=file_path,
        )
