"""Low-level pure functions for scientific computation.

Each function lives in its own file:
- One function per file
- Pure mathematical transformations
- No side effects
- No hidden state
- No access to the catalog (functions accept all parameters; pipelines provide defaults)

Functions are composable building blocks. Pipelines orchestrate them.
"""

from .srgb_to_linear_rgb import srgb_to_linear_rgb
from .linear_rgb_to_xyz import linear_rgb_to_xyz
from .xyz_to_lab import xyz_to_lab

__all__ = [
    "srgb_to_linear_rgb",
    "linear_rgb_to_xyz",
    "xyz_to_lab",
]
