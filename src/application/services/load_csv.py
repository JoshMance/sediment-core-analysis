"""CSV loader — pure I/O service.

Reads a CSV file from disk and returns a pandas DataFrame.
No signals, no Store interaction, no domain logic.

Internal to the application layer (services/).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Extensions recognised by the load pipeline (used by UI file filters)
CSV_EXTENSIONS: tuple[str, ...] = (".csv",)


def load_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV file and return a DataFrame.

    Args:
        path: Path to a CSV file.

    Returns:
        pandas DataFrame with inferred dtypes.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        return pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Could not read CSV '{path.name}': {e}") from e
