"""Image entity for the workspace."""
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
