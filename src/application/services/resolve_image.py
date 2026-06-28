"""Application service — resolves a core entity's display image.

This is the single place in the application layer that bridges raw pixel
data (``CoreEntity.base_data``) and the science-layer filter pipeline.

Callers should generally go through ``AppController.get_resolved_data``
rather than calling this directly, so the controller can maintain its
resolved-image cache.

To add a new filter type
------------------------
1. Write the transform in ``science/lib/filters.py``:
       def my_filter(arr: np.ndarray, value: float) -> np.ndarray: ...
2. Import it here and add it to ``FILTER_REGISTRY``.
That is all — no other files need changing.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from science.lib.filters import brightness, contrast, gamma

# Dispatch table: filter "type" string → science function.
# All functions share the signature: (arr: ndarray, value: float) -> ndarray.
FILTER_REGISTRY: dict[str, Callable[[np.ndarray, float], np.ndarray]] = {
    "brightness": brightness,
    "contrast": contrast,
    "gamma": gamma,
}


def resolve(base_data: np.ndarray, filter_stack: list[dict]) -> np.ndarray:
    """Return the display image: *base_data* with *filter_stack* applied.

    Each entry in *filter_stack* must have:
        ``"type"``     — str key into FILTER_REGISTRY
        ``"value"``    — float parameter passed to the filter function
        ``"enabled"``  — bool (optional, default True); skipped when False

    Returns *base_data* unchanged when *filter_stack* is empty or every
    entry is disabled.
    """
    if not filter_stack:
        return base_data
    result = base_data
    for item in filter_stack:
        if not item.get("enabled", True):
            continue
        fn = FILTER_REGISTRY.get(item["type"])
        if fn is None:
            continue
        result = fn(result, item["value"])
    return result
