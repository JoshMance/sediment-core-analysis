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
        is_draft: True while the core is still being prepared for analysis.
        id: Assigned by the Store on add().
        asset_ref: Archive-relative path to the sidecar PNG (e.g. 'assets/<id>_core.png').
                   Populated by the archive service on load; not set during normal runtime.
    """
    name: str
    data: NDArray[np.uint8] | None = field(default=None, repr=False)
    source_image_id: str | None = None
    is_draft: bool = False
    id: str | None = None
    asset_ref: str | None = None

    def to_dict(self) -> dict:
        """Serialise to a plain dict for session.json.

        Pixel data is NOT included — the archive service writes it as a
        sidecar PNG and stores the path in 'asset_ref'.
        """
        return {
            "id": self.id,
            "name": self.name,
            "source_image_id": self.source_image_id,
            "is_draft": self.is_draft,
            "asset_ref": self.asset_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoreEntity":
        """Reconstruct from a plain dict. Pixel data is not restored here —
        the AppController loads it from the resolved asset path."""
        return cls(
            id=data["id"],
            name=data["name"],
            source_image_id=data.get("source_image_id"),
            is_draft=bool(data.get("is_draft", False)),
            asset_ref=data.get("asset_ref"),
        )
