"""Reference Data Catalog.

Loads and caches reference datasets from science/data/ for use by pipelines.
Provides read-only access to CIE illuminant spectra and other lookup tables.

The catalog is used only by pipelines, never by functions directly.
Functions should remain pure and free of data loading logic.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


# Path to the data directory
DATA_DIR = Path(__file__).parent.parent / "data"


# CIE Standard Illuminant white points (XYZ tristimulus values)
# Reference: http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
_WHITE_POINTS = {
    "C": np.array([0.98074, 1.0, 1.18232], dtype=np.float64),
    "D50": np.array([0.96422, 1.0, 0.82521], dtype=np.float64),
    "D65": np.array([0.95047, 1.0, 1.08883], dtype=np.float64),
}


class DataCatalog:
    """Catalog of reference datasets for scientific computations.
    
    Loads data lazily and caches results for reuse.
    All data is read-only.
    
    Design philosophy: Data-driven and extensible.
    - Use lookup tables and generic accessors, not hardcoded methods
    - Adding new data should not require code changes
    - Functions should accept parameters; pipelines provide values via catalog
    """
    
    @staticmethod
    @lru_cache(maxsize=8)
    def cie_illuminant(name: str) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Load a CIE standard illuminant spectrum.
        
        Args:
            name: Illuminant name ('C', 'D50', or 'D65')
            
        Returns:
            Tuple of (wavelengths, spectral_power) arrays
            - wavelengths: (N,) array of wavelength values in nm
            - spectral_power: (N,) array of relative spectral power
            
        Raises:
            ValueError: If illuminant name is not recognized
            FileNotFoundError: If data file is missing
        """
        illuminant_files = {
            "C": DATA_DIR / "C" / "CIE_illum_C.csv",
            "D50": DATA_DIR / "D50" / "CIE_std_illum_D50.csv",
            "D65": DATA_DIR / "D65" / "CIE_std_illum_D65.csv",
        }
        
        if name not in illuminant_files:
            raise ValueError(f"Unknown illuminant '{name}'. Available: {list(illuminant_files.keys())}")
        
        filepath = illuminant_files[name]
        if not filepath.exists():
            raise FileNotFoundError(f"Illuminant data file not found: {filepath}")
        
        # Load CSV: wavelength, spectral_power
        data = np.loadtxt(filepath, delimiter=",", dtype=np.float64)
        wavelengths = data[:, 0]
        spectral_power = data[:, 1]
        
        return wavelengths, spectral_power
    
    @staticmethod
    def white_point(illuminant: str) -> NDArray[np.float64]:
        """Get the XYZ tristimulus values for a standard illuminant's white point.
        
        Args:
            illuminant: Illuminant name ('C', 'D50', 'D65')
            
        Returns:
            (3,) array [X, Y, Z] for the specified illuminant
            
        Raises:
            ValueError: If illuminant is not recognized
            
        Reference:
            http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
        """
        if illuminant not in _WHITE_POINTS:
            available = list(_WHITE_POINTS.keys())
            raise ValueError(f"Unknown illuminant '{illuminant}'. Available: {available}")
        
        return _WHITE_POINTS[illuminant].copy()
    
    @staticmethod
    def list_illuminants() -> list[str]:
        """Get list of available illuminants.
        
        Returns:
            List of illuminant names (e.g., ['C', 'D50', 'D65'])
        """
        return list(_WHITE_POINTS.keys())


# Shared catalog instance
catalog = DataCatalog()
