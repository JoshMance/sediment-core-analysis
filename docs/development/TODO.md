# Development TODO

## Fix #3: Consolidate Column Type Labels [2026-10-18]

### Issue

Column type labels ("Text", "Number", "Date") are defined in three separate locations:

1. **src/ui/views/panels/dataset_panel/dataset_panel.py** (line 184)
   - `_TYPE_OPTIONS = ["Text", "Number", "Date"]`

2. **src/ui/views/panels/dataset_panel/dataset_panel.py** (lines 49-66)
   - `_parse_cell_value()` method uses `if col_type == "Text"`, `if col_type == "Number"`, etc.

3. **src/application/app_controller.py** (lines 41-46)
   - `_dtype_to_label()` method uses string literals: `"Number"`, `"Date"`, `"Text"`

### Why This Matters

This violates DRY pressure point #6 (data/ui configuration). To add a new column type or rename an existing one requires:

- Updating the list in dataset_panel.py
- Updating the parse logic in dataset_panel.py
- Updating the label mapping in app_controller.py
- Updating any documentation that references these types

This creates multiple opportunities for inconsistency and drift.

### Solution

Create a new module: **src/domain/column_types.py**

```python
"""Column type definitions and utilities.

Single source of truth for column type labels and conversions.
"""

# Valid column type labels
COLUMN_TYPES: list[str] = ["Text", "Number", "Date"]

def parse_cell_value(value: str, col_type: str) -> object:
    """Parse a cell value according to its type."""
    if col_type == "Number":
        try:
            if "." in str(value):
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return None
    elif col_type == "Date":
        # Date parsing logic here
        return value  # placeholder
    else:  # "Text"
        return str(value)

def dtype_to_label(dtype: str) -> str:
    """Map numpy/pandas dtype to user-facing label."""
    if "int" in str(dtype) or "float" in str(dtype):
        return "Number"
    elif "datetime" in str(dtype):
        return "Date"
    else:
        return "Text"
```

### Migration Steps

1. Create src/domain/column_types.py with constants and helper functions
2. Update src/ui/views/panels/dataset_panel/dataset_panel.py:
   - Remove `_TYPE_OPTIONS`
   - Import `COLUMN_TYPES` and use for combo box population
   - Replace `_parse_cell_value()` logic with function from column_types module
3. Update src/application/app_controller.py:
   - Import `dtype_to_label()` from column_types
   - Remove local `_dtype_to_label()` method
4. Add tests in tests/ for column type conversions
5. Update docs/architecture/topology.yaml if needed

### Effort Estimate

Low priority, ~30-45 minutes including tests and verification.

### Links

- Related files: src/ui/views/panels/dataset_panel/dataset_panel.py, src/application/app_controller.py
- Architecture reference: docs/architecture/principles.md (DRY pressure point #6)
