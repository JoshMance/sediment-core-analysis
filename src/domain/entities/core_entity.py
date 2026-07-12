"""CoreEntity — a sediment core sample."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass
class CoreEntity:
    """A sediment core sample.

    Owns its pixel data directly. All image imports are treated as cores,
    and derived cores (crop/split) record lineage to parent cores.

    Attributes:
        name: Display name.
        base_data: Raw core image as an (H, W, 3) uint8 RGB array.  Write-once
                   after import or crop — never mutated.  Callers that need the
                   display image (with filters applied) should use
                   ``AppController.get_resolved_data`` instead.
        source_file_path: Original imported source file path, if any.
        parent_core_id: Parent core id if derived from another core.
        child_core_ids: IDs of cores derived from this core.
        derivation_type: Import/operation type (e.g. 'import', 'crop', 'split').
        derivation_params: Operation metadata payload for reproducibility.
        mm_per_px: Millimetres per pixel. 0.0 means uncalibrated.
        is_draft: True while the core is still being prepared for analysis.
        dataset_plots: Ordered list of dataset columns shown as line plots alongside
                       the core image. Each entry is {'dataset_id': str, 'column_name': str}.
        id: Assigned by the Store on add().
        asset_ref: Archive-relative path to the sidecar PNG (e.g. 'assets/<id>_core.png').
                   Populated by the archive service on load; not set during normal runtime.
    """
    name: str
    base_data: NDArray[np.uint8] | None = field(default=None, repr=False)
    source_file_path: Path | None = None
    parent_core_id: str | None = None
    child_core_ids: list[str] = field(default_factory=list)
    derivation_type: str = "import"
    derivation_params: dict = field(default_factory=dict)
    mm_per_px: float = 0.0
    illuminant: str | None = None
    filter_stack: list[dict] = field(default_factory=list)
    is_draft: bool = False
    dataset_plots: list[dict] = field(default_factory=list)
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
            "source_file_path": str(self.source_file_path) if self.source_file_path is not None else None,
            "parent_core_id": self.parent_core_id,
            "child_core_ids": self.child_core_ids,
            "derivation_type": self.derivation_type,
            "derivation_params": self.derivation_params,
            "mm_per_px": self.mm_per_px,
            "illuminant": self.illuminant,
            "filter_stack": self.filter_stack,
            "is_draft": self.is_draft,
            "dataset_plots": self.dataset_plots,
            "asset_ref": self.asset_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoreEntity":
        """Reconstruct from a plain dict. Pixel data is not restored here —
        the AppController loads it from the resolved asset path."""
        source_file_path = Path(data["source_file_path"]) if data.get("source_file_path") else None
        return cls(
            id=data["id"],
            name=data["name"],
            source_file_path=source_file_path,
            parent_core_id=data.get("parent_core_id"),
            child_core_ids=data.get("child_core_ids", []),
            derivation_type=data.get("derivation_type", "import"),
            derivation_params=data.get("derivation_params", {}),
            mm_per_px=float(data.get("mm_per_px", 0.0)),
            illuminant=data.get("illuminant"),
            filter_stack=list(data.get("filter_stack", [])),
            is_draft=bool(data.get("is_draft", False)),
            dataset_plots=list(data.get("dataset_plots", [])),
            asset_ref=data.get("asset_ref"),
        )
