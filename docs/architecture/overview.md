# Architecture Summary

## Pattern

MVP (Model-View-Presenter) + Command Pattern — idiomatic PySide6

> Why MVP over MVVM? PySide6 QWidgets have no real data binding. `Property()` is
> designed for QML. In practice, QWidget ViewModels end up as Presenters — classes
> that manually wire signals/slots between Views and data.

---

## Layers

The system is organised into three layers. Dependencies flow inward: UI → Application → Domain.

```text
┌─────────────────────────────────────────┐
│  UI Layer          src/ui/              │
│  (Views, Presenters)                    │
├─────────────────────────────────────────┤
│  Application Layer src/application/     │
│  (AppController, Application Services)  │
├─────────────────────────────────────────┤
│  Domain Layer      src/domain/          │
│  (Entities, Store, Domain Services)     │
└─────────────────────────────────────────┘
```

### Science Module (Cross-Cutting) — `/science/`

`science/` is not a fourth architecture layer. It is a top-level module that
owns scientific transformations and reference data (e.g. RGB/CIELAB/Munsell/
calibration transforms).

Any layer may call `science.lib` when needed. Preferred orchestration is still via
Presenter/Application when practical, but the hard rule is: scientific logic
must live in `science`, not be reimplemented elsewhere.

### Domain Layer — `src/domain/`

The innermost layer. Knows nothing about the Application or UI layers.

Contains **Entities** (the domain objects), the **Store** (runtime Entity storage
and change notification), and **Domain Services** (stateless operations that transform entities).

### Application Layer — `src/application/`

Orchestrates use cases. Depends on the Domain layer — may use Domain Services,
read/write the Store, and construct Entities — but the Domain layer never
depends on the Application layer.

Contains the **AppController** (long-lived Component that coordinates user intent)
and **Application Services** (stateless I/O helpers such as an image loader).

Application Services may call Domain Services. Domain Services must **never**
call Application Services.

### UI Layer — `src/ui/`

The outermost layer. Depends on both the Application and Domain layers.

Contains **Presenters** (Components that wire Views to the Store and AppController)
and **Views** (display-only widgets). Views know nothing about the domain or application layers.

---

## Ontology

Three terms that cut across all layers:

| Term          | Definition                                                                                                                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Component** | A key runtime object within the system. Some Components are long-lived (e.g. the AppController or Store), while others such as Views and Presenters may be created and destroyed during execution.                              |
| **Service**   | A stateless unit of application or domain logic responsible for performing operations that do not naturally belong to an Entity. Services are typically instantiated to perform a task and discarded once the task is complete. |
| **Entity**    | A domain object representing something in the problem space, defined primarily by its identity. Entities maintain state over time and may contain simple logic that operates on their state.                                    |

All three layers contain **Components**. **Entities** are defined and stored in the
Domain layer, but the Application layer orchestrates their creation. Both the
Application and Domain layers have their own **Services**, with the dependency
rule that Application Services may use Domain Services but not vice versa.
`science/` remains outside this layering model.

---

## Domain Layer Detail

### Entities — `src/domain/entities/`

> Domain objects defined by identity. Maintain state over time. Plain Python.

| What                        | Implementation                                                         |
| --------------------------- | ---------------------------------------------------------------------- |
| Entity classes (5-10 types) | `dataclasses` (stdlib). No Qt.                                         |
| Business logic on Entities  | Methods on the dataclass, or standalone functions in the same module.  |
| Serialization               | `to_dict()` / `from_dict()` methods on each Entity. Use `json` stdlib. |

### Domain Services — `src/domain/services/`

> Stateless operations that span multiple Entities. Currently a placeholder.

At this scale, Entity logic lives next to the Entity it operates on. Domain
Services will be added as cross-Entity operations emerge.

### Store (Component) — `src/domain/store/`

> Single source of truth. Long-lived Component that holds all runtime Entity instances.

| What                | Implementation                                                                       |
| ------------------- | ------------------------------------------------------------------------------------ |
| Public API          | `QObject` subclass. Facade for all state access.                                     |
| Entity storage      | Delegates to internal `container.py` — `dict[str, Entity]` keyed by ID.              |
| ID assignment       | `uuid.uuid4().hex` assigned on add if Entity has no ID.                              |
| Dependency tracking | Delegates to internal `graph.py` — `dict[str, set[str]]` mapping ID → dependent IDs. |
| Change notification | Qt `Signal` per mutation (e.g. `entityAdded`, `entityRemoved`, `entityUpdated`).     |
| Entity registry     | `domain/entities/registry.py` — explicit `dict[str, type]` of known Entity types.    |

The Store is a `QObject` so it can emit signals directly. No custom Event Bus needed —
Qt's signal/slot system already does topic-based subscriptions.

```python
class Store(QObject):
    entityAdded   = Signal(str, str)  # entity_id, entity_type
    entityRemoved = Signal(str, str)  # entity_id, entity_type
    entityUpdated = Signal(str, str)  # entity_id, entity_type
```

**Internal modules** (`container.py`, `graph.py`, `signal_payloads.py`) are implementation
details — nothing outside `domain/store/` imports them directly.

Presenters connect to Store signals to react to changes. This is the "Event Bus"
without building a custom one.

---

## Application Layer Detail

### AppController (Component) — `src/application/`

> Long-lived Component. Receives user intent from Presenters, performs I/O via
> Application Services, constructs Entities, and writes to the Store.

| What              | Implementation                                                                           |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Orchestration     | Plain Python class. Presenters call methods on it directly.                              |
| I/O               | Delegates to Application Services — stateless helpers (e.g. `load_image.py`)             |
| Business logic    | Calls Entity methods/functions for validation or transformation before writing to Store. |
| Session save/load | Owns `.sedivis` file persistence — reads Store state to save, populates Store on load.   |
| Undo/redo         | Will own a `QUndoStack` (not yet implemented).                                           |

```python
class AppController:
    def __init__(self, store, workspace_state=None, component_watcher=None):
        self._store = store
        self._workspace_state = workspace_state
        self._component_watcher = component_watcher
        self.status_context = StatusContext()
        self.ribbon_context = RibbonContext()
        self.recent_dirs = RecentDirs()

    def create_image_entity(self, file_path: str) -> str:
        data = load_image(file_path)          # services/load_image.py
        entity = ImageEntity(name=..., data=data)
        return self._store.add(entity)        # Store emits entityAdded

    def open_in_workspace(self, entity_id: str) -> None:
        workspace_service.open_entity(entity_id, self._store, self._workspace_state)
```

**Internal modules:** `services/` is internal to the Application package — nothing
outside `application/` imports a Service directly, just like `container.py` is internal to `domain/store/`.

**File Operations:** The AppController owns `.sedivis` session persistence. It reads
all state from the Store to save, and clears + populates the Store on load.
The Store itself knows nothing about files or serialization.

### Application Services — `src/application/services/`

> Stateless helpers for I/O and external concerns. Internal to the Application layer.

Currently contains:

- `load_image.py` — reads image files via `imageio.v3`.
- `workspace_service.py` — maps entity types to panel types and calls `WorkspaceState.open`.
- `session_archive.py` — reads/writes `.sedivis` ZIP archives containing entities, workspace state, and bundled assets.

### WorkspaceState (Component) — `src/application/workspace_state.py`

> Application-layer record of which panels are currently open. Long-lived QObject — not a widget.

| What               | Implementation                                                          |
| ------------------ | ----------------------------------------------------------------------- |
| Panel tracking     | `_open: dict[str, WorkspaceEntry]` keyed by `entity_id`                 |
| `open(entry)`      | Emits `panelAdded` on first open; `panelFocusRequested` if already open |
| `close(entity_id)` | Removes entry, emits `panelRemoved`                                     |

```python
class WorkspaceState(QObject):
    panelAdded          = Signal(object)  # WorkspaceEntry
    panelRemoved        = Signal(str)     # entity_id
    panelFocusRequested = Signal(str)     # entity_id — already open, just focus it
```

The UI layer (`WorkspacePresenter`) connects to these signals to create, destroy, and focus panel widgets.

---

## UI Layer Detail

### Presenters (Components, one per panel/sidebar) — `src/ui/presenters/`

> Components that wire a View to the Store and AppController. Created/destroyed
> with their View. Translate UI events into AppController calls.

| What         | Implementation                                                     |
| ------------ | ------------------------------------------------------------------ |
| Base class   | `QObject` (PySide6).                                               |
| Reads data   | Connects to Store signals. Reads Store directly for current state. |
| Writes data  | Calls AppController methods. Never writes to Store directly.       |
| Updates View | Calls methods on its View to refresh display.                      |

```python
class EntityListPresenter(QObject):
    def __init__(self, view: EntityListView, store: Store, controller: AppController):
        self.view = view
        self.store = store
        self.controller = controller

        # Listen to Store changes
        self.store.entityAdded.connect(self._on_entity_added)
        self.store.entityRemoved.connect(self._on_entity_removed)

        # Listen to View events
        self.view.delete_requested.connect(self._on_delete_requested)

    def _on_entity_added(self, entity_id: str):
        entity = self.store.get(entity_id)
        self.view.add_item(entity_id, entity.name)

    def _on_delete_requested(self, entity_id: str):
        self.controller.delete_entity(entity_id)  # Goes through undo stack
```

Presenters don't talk to each other. They both listen to the same Store signals
and react independently.

### Views (Components, dumb widgets) — `src/ui/views/`

> Display-only Components. Emit signals for user actions. Know nothing about the domain.

**Pragmatic pattern:** Views handle OS interactions (file dialogs, etc.) but emit raw inputs (`fileSelected(path)`) not domain conclusions (`createCoreAnalysis(...)`). Presenter interprets domain meaning.

| What           | Implementation                                                                                        |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| Main window    | `QMainWindow` with nested `QVBoxLayout` / `QHBoxLayout` for fixed layout.                             |
| Shell views    | Custom `QWidget` subclasses in `shell/`.                                                              |
| Runtime panels | Custom `QWidget` subclasses in `panels/`.                                                             |
| Lists/trees    | `QListWidget`, `QTreeWidget` (simple), or `QListView`/`QTreeView` + `QAbstractItemModel` (if needed). |
| Menus/toolbars | `QMenuBar`, `QToolBar`, `QAction`. Undo/redo actions from `QUndoStack.createUndoAction()`.            |

**`shell/` vs `panels/` — the key structural rule:**

| Folder    | Rule                                                                                           | Examples                                                                |
| --------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `shell/`  | Views that are **created at startup and persist** for the lifetime of the application.         | `Ribbon`, `VariablesList`, `PreviewPanel`, `StatusBar`, `WorkspaceView` |
| `panels/` | Views that are **created at runtime** on demand (e.g. when the user opens or creates a thing). | `ImagePanel`, `CoreStudioPanel`, entity editors                         |

Nothing in `shell/` is created or destroyed while the app is running. Nothing in `panels/` exists at startup.

### Styling — `src/ui/resources/theme/`

| File          | Purpose                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------- |
| `colors.py`   | Token dicts `DARK` and `LIGHT` — the single source of truth for all colours                        |
| `dark.qss`    | Dark stylesheet using `@token_name` placeholders                                                   |
| `light.qss`   | Light stylesheet using `@token_name` placeholders                                                  |
| `apply.py`    | `apply_theme(app, *, dark)` — loads the right QSS, substitutes tokens, calls `app.setStyleSheet()` |
| `__init__.py` | Re-exports `apply_theme` so callers import from `src.ui.resources.theme`                           |

All visual styling lives in `dark.qss` / `light.qss`, applied once at startup via
`app.setStyleSheet()`. This means themes can be switched without touching any View code.

To change a colour, edit `colors.py` only — the change propagates to both QSS files automatically.

**Rules:**

- Prefer QSS roles (`objectName` / dynamic properties) over inline styling.
- Limited inline `setStyleSheet()` use is allowed only for tiny, local visual tweaks.
- Inline styling must not define theme-level colour systems, typography policy, or reusable roles.
- If a widget needs a distinct visual role (e.g. error state, primary action button),
  the View sets a Qt property or `objectName`; the appearance is defined in the QSS.

```python
# View sets role — QSS defines its appearance
button.setObjectName("primaryAction")
field.setProperty("state", "error")
field.style().unpolish(field)   # force QSS re-evaluation after property change
field.style().polish(field)
```

```qss
/* dark.qss */
QPushButton#primaryAction { background: @accent; color: @on_accent; }
QLineEdit[state="error"]  { border: 1px solid #e81123; }
```

---

## Testing Strategy

| What             | Implementation                                                       |
| ---------------- | -------------------------------------------------------------------- |
| **Manual tests** | `tests/` - Component verification ending in `_test.py`               |
| Test structure   | Flat structure with helpers/ subdirectory                            |
| Purpose          | Manual testing for view components and some non-UI component testing |

**Current testing approach**:

We use manual tests for view-related components with some testing for non-UI components.
We acknowledge this testing approach isn't perfect, but we will evolve into a more
exact manual/automated testing distinction as the application grows.

**Manual tests** (`tests/`):

- Test files end in `_test.py` in flat structure
- Visual verification and component logic testing
- Example: `file_browser_test.py` tests view components
  - Example: `file_browser_presenter_test.py` tests presenter logic with views
- Example: `image_loading_test.py` tests full chain: View → Presenter → AppController → Store
- Example: `container_test.py` tests entity container CRUD (no Qt)
- Helpers: Shared DRY components in `tests/helpers/`
  **Dev mode** (`--dev` flag):

Running `uv run python main.py --dev` opens a second window (DevLog) that
auto-discovers and logs every Qt signal emitted by any watched Component.
The AppController receives a `component_watcher` callback so Components
created at runtime are also logged without changing main.py.

DevLog lives in `tests/helpers/dev_log.py` -- it's debugging infrastructure,
not application code, so it stays outside the three layers.
**Test organization**: Flat structure for simplicity with descriptive filenames.

**Deferred:** Async/threading strategy and comprehensive error handling will be
added as the application grows beyond initial development.

---

## PySide6 Classes Used

| PySide6 Class                 | Where                                  | Purpose                  |
| ----------------------------- | -------------------------------------- | ------------------------ |
| `QApplication`                | App entry point                        | Event loop               |
| `QMainWindow`                 | Root View                              | Central widget, menus    |
| `QWidget`                     | Panel contents                         | Custom panel interiors   |
| `QListWidget` / `QTreeWidget` | Views                                  | Simple list/tree display |
| `QUndoStack`                  | AppController                          | Undo/redo management     |
| `QUndoCommand`                | AppController                          | Each undoable action     |
| `QTabWidget`                  | WorkspaceView                          | Tabbed panel host        |
| `QObject`                     | Store, Presenters, WorkspaceState      | Signals/slots            |
| `Signal` / `Slot`             | Store → Presenters, Views → Presenters | Communication            |
| `QAction`                     | Views                                  | Menu/toolbar items       |
| `QFileDialog`                 | App                                    | Open/save dialogs        |

## Self-Designed

| What                    | Kind      | Notes                                                                             |
| ----------------------- | --------- | --------------------------------------------------------------------------------- |
| CalibrationEntity       | Entity    | `dataclasses`, spatial calibration (`mm_per_px`)                                  |
| Entity classes          | Entity    | `dataclasses`, with `to_dict()`/`from_dict()`                                     |
| Store                   | Component | `QObject` + dict. Emits signals on change.                                        |
| AppController           | Component | Plain class. Calls Services, constructs Entities, writes to Store.                |
| Application Services    | Service   | Stateless. Internal to `application/`. E.g. image loading.                        |
| QUndoCommand subclasses | —         | One per mutation type (planned).                                                  |
| Presenters              | Component | One per panel. Wires Store ↔ View.                                                |
| Views                   | Component | PySide6 widgets. Display only.                                                    |
| Session serializer      | Service   | `json.dump`/`json.load` with Entity `to_dict()`/`from_dict()`.                    |
| Core Studio panel       | Component | Column-based panel (depth, image, layers, RGB, CIELab) with toolbar and drag-drop |

Science module notes:

- Science library modules: reusable modules in `science/lib/` (for example, `munsell.py`).
- Science reference data: static JSON files in `science/data/`.

## Third-Party Libraries

| Library                | Purpose                    | Verdict                                                                      |
| ---------------------- | -------------------------- | ---------------------------------------------------------------------------- |
| `dataclasses` (stdlib) | Entity definitions         | Use.                                                                         |
| `json` (stdlib)        | File save/load             | Use.                                                                         |
| `uuid` (stdlib)        | Entity IDs                 | Use.                                                                         |
| `imageio`              | Image file loading         | Use. AppController's `services/load_image.py` reads images via `imageio.v3`. |
| `numpy`                | Array data                 | Use. Image pixel data stored as `NDArray[np.uint8]`.                         |
| `pydantic`             | Validation + serialization | Optional. Useful if entities have complex validation.                        |
| Everything else        | —                          | Not needed at this scale.                                                    |

---

## Data Flow

```text
User clicks "Load Image" in the Ribbon
  → Ribbon emits buttonClicked("Load Image")
  → RibbonPresenter opens a QFileDialog (starting in recent_dirs "image" directory)
  → User selects a file; RibbonPresenter records the directory via recent_dirs
  → RibbonPresenter calls controller.create_image_entity(path)
  → AppController calls load_image(path) → pixel data
  → AppController constructs ImageEntity(name, file_path, data)
  → AppController calls store.add(entity)
  → Store assigns UUID, stores entity, emits entityAdded(id, type)
  → All Presenters listening to entityAdded react
  → Each Presenter updates its View
```

```text
User clicks delete button (planned)
  → View emits delete_requested signal (entity_id)
  → Presenter calls controller.delete_entity(entity_id)
  → AppController removes entity from Store
  → Store emits entityRemoved signal (entity_id)
  → Presenters react, Views update
```

```text
User double-clicks an entity in VariablesList
  → VariablesList emits entityOpenRequested(entity_id)
  → VariablesPresenter calls controller.open_in_workspace(entity_id)
  → AppController calls workspace_service.open_entity(entity_id, store, workspace_state)
  → WorkspaceService maps entity type → panel type ("ImageEntity" → "ImagePanel")
  → WorkspaceService calls workspace_state.open(WorkspaceEntry(...))
  → WorkspaceState emits panelAdded(entry)  [or panelFocusRequested if already open]
  → WorkspacePresenter receives panelAdded, calls factory, creates (ImagePanel, ImagePanelPresenter)
  → WorkspacePresenter calls workspace_view.add_tab(panel, title, entity_id)
  → ImagePanelPresenter loads entity from Store, converts to QPixmap, calls panel.set_pixmap()
```

```text
User crops a region in ImagePanel
  → ImagePanel emits cropConfirmed(pixmap)
  → ImagePanelPresenter converts QPixmap → numpy array
  → ImagePanelPresenter calls controller.create_cropped_image(name, data, parent_id)
  → AppController creates ImageEntity with parent_id, inherits calibration_id from parent
  → AppController appends child_id to parent’s child_ids via store.update_field
  → Store emits entityAdded (new child) + entityUpdated (parent)
  → VariablesList reacts, shows new cropped image in the entity list
```

```text
User right-clicks an image in VariablesList and chooses "Open In Core Studio"
  → VariablesList emits openInCoreStudioRequested(image_id)
  → VariablesPresenter calls controller.create_draft_core_from_image(image_id)
  → VariablesPresenter calls controller.open_core_in_studio(core_id)
  → WorkspaceState emits panelAdded (or panelFocusRequested if this core tab is already open)
  → WorkspacePresenter creates CoreStudioPanel + CoreStudioPresenter bound to core_id
  → Core Studio opens for that core (at most one panel per CoreEntity)
```

## Key Rules

1. **Layer dependencies flow inward** — UI → Application → Domain, never the reverse. `science/` is cross-cutting and may be called by any layer.
2. **Application Services may use Domain Services** — Domain Services must never use Application Services
3. **Presenters never talk to each other** — they independently listen to Store signals
4. **Presenters can read the Store** — only AppController can write it
5. **Only AppController writes to Store** — undo/redo via QUndoCommand planned
6. **Views are dumb** — they emit signals for user actions, display what Presenters tell them
7. **No custom Event Bus** — Store's Qt signals serve the same purpose
8. **Domain Services placeholder** — `domain/services/` exists for entity specific transformations
9. Services raise exceptions. The orchestrator decides what to do. That keeps the service reusable and the policy in one place.
10. **Shell vs Panels** — views in `shell/` are created at startup and persist; views in `panels/` are created at runtime on demand. Never put a startup view in `panels/`, never put a runtime view in `shell/`.
11. **Science module ownership** — scientific transformations (RGB/LAB/Munsell/calibration transforms) live in top-level `science/` as the single source of truth.
12. **View boundary for science** — views may read pixels and compute display geometry from provided parameters, but they do not decide scientific parameters.
