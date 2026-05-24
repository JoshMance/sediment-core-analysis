# Science Module

This module is the single source of truth for science logic and science-owned reference data.

## Layout

```text
science/
  README.md
  lib/
  data/
  scripts/
```

## Rules

- `data/`: static reference datasets only. Subfolders are allowed and encouraged when organizing by topic. Keep directory depth shallow; one folder layer under `data/` is the preferred default.
- `lib/`: reusable functions and transformations. These can be used by the app and by `scripts/`.
- `scripts/`: science-internal workflows, investigations, demos, and longer context-specific tasks.

Current `data/` usage includes reference datasets and colorimetry constants consumed by `lib/` transforms.

`lib/` code should generally be fast, composable, and self-contained. `scripts/` can be slower and more exploratory.

## Transform Contracts

- Inputs are typically RGB-first in this project. Most workflows start from RGB image data and derive XYZ/CIELAB from there.
- XYZ is represented in relative scale where white has `Y = 1.0`, matching the active colorimetry profile in `science/data/colorimetry/`.
- `xyz_to_rgb` uses clipping before uint8 output. Out-of-gamut XYZ values are clipped to the valid RGB range by design for stable display output.

## Packaging Note

Current data loading uses source-tree path resolution, which is fine for local development and current app execution. If this module is later distributed as an installable package or packaged executable where resource paths may differ, migrate data loading to `importlib.resources`.
