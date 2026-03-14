# Manual Test: CSV Loading

## Overview

Allows the user to load a `.csv` file from disk via the workspace file browser. The file is parsed by the application service layer into a pandas DataFrame, stored in the domain `Store` as a `CsvEntity`, and displayed in a `CsvPanel` tab where cells and column metadata can be edited.

---

## Files Involved

| File                                         | Role                                                                                                                                                     |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/application/services/load_csv.py`       | Pure I/O service: reads a `.csv` file from disk using `pd.read_csv()`, returns a `DataFrame`. Raises `FileNotFoundError` or `ValueError` on failure.     |
| `src/domain/entities/csv_entity.py`          | Domain entity that wraps the DataFrame and its column type metadata.                                                                                     |
| `src/ui/views/panels/csv_panel/csv_panel.py` | View: `CsvPanel` widget containing a `QTableView` backed by a custom `_DataFrameTableModel`. Emits signals for all user edits; contains no domain logic. |
| `src/ui/presenters/csv_panel_presenter.py`   | Presenter: wires `CsvPanel` to the `Store` and `AppController`. Created by `WorkspacePresenter` when a CSV tab is opened.                                |

---

## Architecture Notes

- **`load_csv_panel_presenter.py` is ephemeral** — it is created per-tab by `WorkspacePresenter` and destroyed with it. One presenter instance exists per open CSV tab.
- **`Store.entityUpdated` signal** — the presenter subscribes to this and refreshes the view whenever the store reports a change to its entity ID. This means external mutations (e.g., from a programmatic update) will also reflect in the panel.
- **Column types** — the panel receives column type metadata separately from the DataFrame. These are displayed and can be changed via right-click context menu on column headers.
- **Cell edits** — `cellEdited(row, col, value)` fires immediately on edit commit; the presenter forwards to `AppController.update_csv_cell()`.
- **`pd.read_csv` with inferred dtypes** — no dtype coercion is applied at load time; pandas infers types from file content.

---

## Design Decisions

- The load service (`load_csv.py`) is intentionally thin — no signals, no Store interaction, no domain knowledge. It is called by the application layer during the file-open flow.
- `FileNotFoundError` and `ValueError` are raised (not swallowed) so the presenter or controller can surface them as user-visible errors.
- Column rename and type-change operations go through the `AppController` (not mutated directly on the view model) to ensure Store consistency.
- The `_DataFrameTableModel` is private to `csv_panel.py` — it is never imported elsewhere.
- NaN values display as empty string in the view but return `None` in edit role, preserving the distinction between empty and NaN.

---

## Manual Test Checklist

### Loading a file

- [ ] Open the application. Use the workspace file browser to open a `.csv` file.
- [ ] A new tab appears in the main panel area labelled with the filename.
- [ ] The tab's table view shows the correct number of rows and columns from the file.
- [ ] Column headers match the CSV's first row (or auto-generated headers if the file has none).
- [ ] Data values in cells match the source file.

### Data types

- [ ] Open a CSV with a mix of integer, float, and string columns — verify pandas inferred types appear correctly in the panel's column type indicators.
- [ ] Open a CSV with all-string data — no crash; strings display as-is.
- [ ] Open a CSV containing `NaN` or blank cells — blank cells display as empty, not `"nan"`.

### Cell editing

- [ ] Double-click a cell to enter edit mode — the cell becomes editable.
- [ ] Type a new value and press Enter — the cell updates, and the change is committed to the Store (verify by reopening or inspecting `Store.get(entity_id).data`).
- [ ] Press Escape during editing — the original value is restored without modification.
- [ ] Edit a numeric cell with a non-numeric string — verify the application handles the type mismatch gracefully (error message or rejection, no crash).

### Column rename

- [ ] Right-click a column header → rename — input dialog appears.
- [ ] Enter a new name and confirm — the column header updates in the view.
- [ ] The change is reflected in the Store entity.
- [ ] Try renaming to a name that already exists — verify graceful handling (rejection or error, no crash or silent duplicate).
- [ ] Cancel the rename dialog — column name unchanged.

### Column type change

- [ ] Right-click a column header → change type — a type selection appears.
- [ ] Select a compatible type (e.g., int column → float) — column updates without error.
- [ ] Select an incompatible type (e.g., string column → int where non-numeric values exist) — graceful error or rejection, no crash.

### Store reactivity

- [ ] With a CSV tab open, trigger a programmatic `Store.entityUpdated` for the entity — the panel refreshes automatically (tests the `_on_entity_updated` path).
- [ ] Open two CSV tabs for different files — edits in one tab do not affect the other (entity IDs are distinct).

### Error handling

- [ ] Attempt to open a file with a `.csv` extension that contains malformed content (e.g., mismatched quotes, binary data) — verify a user-visible error is shown and the application does not crash.
- [ ] Attempt to open a non-existent path programmatically — `FileNotFoundError` is raised and handled.

### Tab lifecycle

- [ ] Open a CSV file, close the tab — no crash, no memory leak (presenter is destroyed with the tab).
- [ ] Re-open the same file after closing — a fresh tab with correct data appears.
- [ ] Open multiple CSV files simultaneously — each has its own independent tab, view, and presenter.
