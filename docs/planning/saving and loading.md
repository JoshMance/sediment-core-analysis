# Saving and Loading `.sedivis` Files

## Goal

A `.sedivis` file is a portable, self-contained project archive. One file contains everything: entity state, workspace state, and all required assets (source images). It can move between machines without breaking.

---

## File Format

A `.sedivis` file is a **ZIP archive** with the following internal structure:

```
project.sedivis  (ZIP)
├── manifest.json        ← format name + version number
├── session.json         ← serialized entities + workspace state
└── assets/
    ├── <id>_source.tif  ← bundled source images (ImageEntity)
    ├── <id>_core.png    ← sidecar pixel data (CoreEntity)
    └── ...
```

**`manifest.json`** — identifies the file format and version. Used for validation and future migration support.

```json
{ "format": "sedivis", "version": 1 }
```

**`session.json`** — structured project state: serialized entities, workspace state, and asset references.

**`assets/`** — all files the project depends on, copied in at save time. Runtime never depends on the original OS path.

---

## Serialization

### Entities

Every entity type gets `to_dict()` / `from_dict()` methods. These write to / read from `session.json`.

- **`ImageEntity`** — `file_path` is saved as provenance only. The archive service copies the image into `assets/` and the saved record points at the bundled asset path (`assets/<id>_source.tif`). New fields `parent_id`, `child_ids`, and `calibration_id` are serialized in the JSON record. For cropped images (no `file_path`), pixel data is encoded as a sidecar PNG (`assets/<id>_image.png`).
- **`CoreEntity`** — has no file path; holds raw pixel data. Saved as a sidecar PNG in `assets/` (`assets/<id>_core.png`). `to_dict()` omits `data` and stores `asset_ref` instead. The archive service writes/reads the PNG.
- **`CalibrationEntity`** — pure JSON, no sidecar assets. `to_dict()` / `from_dict()` serialize `id` and `mm_per_px` directly into `session.json`.

### Workspace State

`WorkspaceEntry` (already a `@dataclass` with `entity_id` and `panel_type`) gets `to_dict()` / `from_dict()`. The list of open entries is written into `session.json` alongside the entity list.

### Registry-based reconstruction

On load, the loader reads the `"type"` field from each entity record and dispatches to the correct class:

```python
ENTITY_TYPES[record["type"]].from_dict(record["data"])
```

No structural changes to `registry.py` are needed — it already maps type name strings to classes.

---

## Architecture Placement

| Concern                                        | Owner                        | Rule                                                                               |
| ---------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------- |
| Serialization format (`to_dict`/`from_dict`)   | Entities + `WorkspaceEntry`  | Domain layer, pure Python                                                          |
| ZIP read/write, asset bundling, path rewriting | `session_archive.py` service | Application service — stateless, raises on error                                   |
| Orchestration (save/load/new flow)             | `AppController`              | Sole writer to Store; owns session temp dir lifetime                               |
| Store clear                                    | `Store.clear()`              | Domain layer (TODO already noted)                                                  |
| Workspace clear                                | `WorkspaceState.clear()`     | Application layer                                                                  |
| File dialogs + menu actions                    | Shell View + Presenter       | UI layer only — Views emit intent, Presenters call AppController                   |
| `.sedivis` file icon in dialogs                | `SedivisIconProvider`        | UI resource — subclasses `QFileIconProvider`, returned by non-native `QFileDialog` |

---

## Save Flow

1. `AppController.save_session(path)` is called by the Presenter.
2. AppController reads all entities from the Store and workspace entries from `WorkspaceState`.
3. Calls `session_archive.save(path, entities, workspace_entries)`.
4. Archive service: writes `manifest.json`, serializes entities to `session.json`, copies required asset files into `assets/`, rewrites asset references to bundled paths, writes the ZIP.

## Load Flow

1. `AppController.load_session(path)` is called by the Presenter.
2. AppController calls `Store.clear()` and `WorkspaceState.clear()` to reset current state.
3. Cleans up any previous temp dir; creates a new `TemporaryDirectory` (owned by AppController).
4. Calls `session_archive.load(path, extract_dir)`.
5. Archive service: validates `manifest.json`, extracts archive to temp dir, parses `session.json`, reconstructs entities via registry, resolves asset references to extracted file paths.
6. AppController adds reconstructed entities to the Store and reopens workspace panels.

**The temp dir is owned by `AppController`** and lives for the duration of the session. It is cleaned up on `new_session()` or app close.

---

## Error Handling

The archive service **raises** on: wrong format, unsupported version, missing JSON, corrupt ZIP, missing bundled assets.

The `AppController` catches and **decides policy**: show an error dialog (via a signal or callback), leave state unchanged if load fails.

---

## File Dialogs and Icon

Open and Save dialogs are created as **non-native** `QFileDialog` instances (i.e. Qt-rendered, not the OS shell dialog). This is required because:

- `QFileDialog.setIconProvider()` is honoured only by the Qt-rendered dialog; the Windows shell dialog ignores it.
- Non-native mode still honours `setDefaultSuffix`, `setNameFilter`, and all standard `QFileDialog` options.

`SedivisIconProvider` (`src/ui/resources/icon_provider.py`) subclasses `QFileIconProvider` and overrides `icon()`: when the file being listed has a `.sedivis` suffix it returns a `QIcon` backed by `src/ui/resources/logo/sedivis_file_icon.svg`; all other file types fall through to the default provider.

```
src/ui/resources/
├── icon_provider.py          ← SedivisIconProvider
└── logo/
    └── sedivis_file_icon.svg ← source artwork
```

The `RibbonPresenter._make_file_dialog()` helper constructs the dialog, sets `DontUseNativeDialog`, and calls `setIconProvider(SedivisIconProvider())` before the dialog is shown.

---

## Build Phases

| Phase               | Work                                                                                          | Independently testable?           |
| ------------------- | --------------------------------------------------------------------------------------------- | --------------------------------- |
| 1 — Serialization   | `to_dict` / `from_dict` on `ImageEntity`, `CoreEntity`, `WorkspaceEntry`                      | Yes — pure Python unit tests      |
| 2 — Infrastructure  | `Store.clear()` + reset signal, `WorkspaceState.clear()`                                      | Yes                               |
| 3 — Archive service | `session_archive.py` — ZIP read/write, asset bundling, path rewriting                         | Yes — file I/O tests              |
| 4 — AppController   | `save_session`, `load_session`, `new_session`, temp dir management                            | Yes — controller integration test |
| 5 — UI wiring       | Ribbon buttons (New / Open / Save / Save As), non-native `QFileDialog`, `SedivisIconProvider` | Manual smoke test                 |

---

## New Code Required

| File                                          | Status                                                                             |
| --------------------------------------------- | ---------------------------------------------------------------------------------- |
| `src/application/services/session_archive.py` | New                                                                                |
| `src/domain/entities/image_entity.py`         | Add `to_dict` / `from_dict`                                                        |
| `src/domain/entities/core_entity.py`          | Add `to_dict` / `from_dict`                                                        |
| `src/application/workspace_state.py`          | Add `clear()` to `WorkspaceState`; add `to_dict` / `from_dict` to `WorkspaceEntry` |
| `src/domain/store/store.py`                   | Add `clear()` + `storeReset` signal (TODO already exists)                          |
| `src/application/app_controller.py`           | Add `save_session`, `load_session`, `new_session`; own temp dir                    |
| `src/ui/views/shell/ribbon/ribbon.py`         | Add New and Save As buttons to File group                                          |
| `src/ui/presenters/ribbon_presenter.py`       | Wire New / Open / Save / Save As to AppController; use non-native dialogs          |
| `src/ui/resources/icon_provider.py`           | New — `SedivisIconProvider`                                                        |
