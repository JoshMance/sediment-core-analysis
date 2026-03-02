"""Public API for science library.

This is the ONLY module that should be imported from outside the science package.
The rest of the application should never import from science/functions/, 
science/pipelines/, or science/catalog/ directly.

Structure:
- functions/  → small, pure mathematical transformations (one function per file)
- pipelines/  → higher-level workflows that orchestrate functions and handle array operations
- catalog/    → loads reference data for use by pipelines
- data/       → packaged reference datasets (constants, lookup tables)

Function vs Pipeline:
- Functions: Pure math, single transformations, accept all parameters
- Pipelines: Orchestrate functions, handle array structures, may use catalog for defaults

Usage:
    from science.api import mean_rgb_per_row, rgb_to_lab, catalog
"""
from __future__ import annotations

# Pipelines (exported as main API)
from .pipelines.mean_rgb_per_row import mean_rgb_per_row
from .pipelines.mean_rgb_for_range import mean_rgb_for_range
from .pipelines.rgb_to_lab import rgb_to_lab

# Individual functions (for advanced use or testing)
from .functions.srgb_to_linear_rgb import srgb_to_linear_rgb
from .functions.linear_rgb_to_xyz import linear_rgb_to_xyz
from .functions.xyz_to_lab import xyz_to_lab

# Catalog (reference data access)
from .catalog import catalog

__all__ = [
    # Pipelines (primary API)
    "mean_rgb_per_row",
    "mean_rgb_for_range",
    "rgb_to_lab",
    # Functions (for advanced use)
    "srgb_to_linear_rgb",
    "linear_rgb_to_xyz",
    "xyz_to_lab",
    # Catalog
    "catalog",
]
