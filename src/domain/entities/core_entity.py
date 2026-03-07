"""CoreEntity — a sediment core sample."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class CoreEntity:
    """A sediment core sample.

    Owns its pixel data directly — the image IS the core (typically cropped
    from a source ImageEntity). source_image_id records provenance but is not
    a live reference; the pixel data stands alone.

    Attributes:
        name: Display name.
        data: Cropped core image as an (H, W, 3) uint8 RGB array.
        source_image_id: ID of the ImageEntity this was cropped from, if any.
        id: Assigned by the Store on add().
    """
    name: str
    data: NDArray[np.uint8] | None = field(default=None, repr=False)
    source_image_id: str | None = None
    id: str | None = None
