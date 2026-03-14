"""CsvEntity — a tabular data set imported from a CSV file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class CsvEntity:
    """A tabular data set.

    Owns a pandas DataFrame plus metadata about column names and types.
    The DataFrame is the authoritative state; columns and column_types
    are derived from it on creation and kept in sync by the AppController.

    Attributes:
        name: Display name.
        data: The tabular data as a pandas DataFrame.
        columns: Ordered list of column names (mirrors df.columns).
        column_types: Mapping of column name → dtype string (e.g. "float64").
        file_path: Original source path (provenance only).
        id: Assigned by the Store on add().
        asset_ref: Archive-relative path to the bundled CSV (e.g. 'assets/<id>_data.csv').
                   Populated by the archive service on load; not set during normal runtime.
    """
    name: str
    data: "pd.DataFrame | None" = field(default=None, repr=False)
    columns: list[str] = field(default_factory=list)
    column_types: dict[str, str] = field(default_factory=dict)
    file_path: Path | None = None
    id: str | None = None
    asset_ref: str | None = None

    def to_dict(self) -> dict:
        """Serialise to a plain dict for session.json.

        DataFrame is NOT included — the archive service writes it as a
        sidecar CSV and stores the path in 'asset_ref'.
        """
        return {
            "id": self.id,
            "name": self.name,
            "columns": self.columns,
            "column_types": self.column_types,
            "file_path": str(self.file_path) if self.file_path is not None else None,
            "asset_ref": self.asset_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CsvEntity":
        """Reconstruct from a plain dict. DataFrame is not restored here —
        the AppController loads it from the resolved asset path."""
        file_path = Path(data["file_path"]) if data.get("file_path") else None
        return cls(
            id=data["id"],
            name=data["name"],
            columns=data.get("columns", []),
            column_types=data.get("column_types", {}),
            file_path=file_path,
            asset_ref=data.get("asset_ref"),
        )
