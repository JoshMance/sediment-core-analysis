"""Science library - pure compute functions for sediment analysis.

This module contains I/O-free compute functions organized as:
- functions/: low-level pure functions
- pipelines/: compositions of functions
- api: the only public import point

Usage:
    from science import api
    rgb = api.mean_rgb_per_row(image_array)
"""
