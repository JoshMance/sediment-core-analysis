"""Image data type for the workspace."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass
class Image:
    """An image item in the workspace.
    
    Attributes:
        name: Display name of the image
        file_path: Path to the image file (or None if not saved)
        data: The image data as an (n, m, 3) numpy array (RGB)
    """
    name: str
    file_path: Path | None = None
    data: NDArray[np.uint8] | None = field(default=None, repr=False)

    @property
    def shape(self) -> tuple[int, int, int] | None:
        """Return the shape of the image data (height, width, channels)."""
        if self.data is not None:
            return self.data.shape
        return None
