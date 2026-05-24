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

`lib/` code should generally be fast, composable, and self-contained. `scripts/` can be slower and more exploratory.
