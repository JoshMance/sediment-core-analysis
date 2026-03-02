# Architecture Summary

## Pattern

MVP (Model-View-Presenter) + Command Pattern — idiomatic PySide6

> Why MVP over MVVM? PySide6 QWidgets have no real data binding. `Property()` is
> designed for QML. In practice, QWidget ViewModels end up as Presenters — classes
> that manually wire signals/slots between Views and data. Calling it MVP is honest
> about what you're actually building.

---

## Components

### 1. Entities (Model)

> Your domain data. Plain Python.

| What                        | Implementation                                                         |
| --------------------------- | ---------------------------------------------------------------------- |
| Entity classes (5-10 types) | `dataclasses` (stdlib). No Qt.                                         |
| Business logic on entities  | Methods on the dataclass, or standalone functions in the same module.  |
| Serialization               | `to_dict()` / `from_dict()` methods on each entity. Use `json` stdlib. |

No separate "Domain Services" layer. At this scale, a function next to the entity
it operates on is clearer than a Services directory with one method per file.

---

### 2. Store

> Single source of truth. Holds all runtime entity instances.

| What                | Implementation                                                                        |
| ------------------- | ------------------------------------------------------------------------------------- |
| Entity storage      | `QObject` subclass with a `dict[str, Entity]` keyed by ID.                            |
| ID assignment       | `uuid.uuid4()` or sequential int counter.                                             |
| Dependency tracking | `dict[str, set[str]]` mapping entity ID → dependent IDs.                              |
| Change notification | Qt `Signal` per event type (e.g. `entity_added`, `entity_removed`, `entity_changed`). |
| Session save/load   | `save_session(path)` / `load_session(path)` methods using `json` stdlib.              |

The Store is a `QObject` so it can emit signals directly. No custom Event Bus needed —
Qt's signal/slot system already does topic-based subscriptions.

```python
class Store(QObject):
    entity_added = Signal(str)        # entity_id
    entity_removed = Signal(str)      # entity_id
    entity_changed = Signal(str, str) # entity_id, field_name
```

ViewModels connect to the Store signals they care about. This is the "Event Bus"
without building a custom one.

---

### 3. Controller

> Receives user intent from Presenters, mutates the Store, handles undo/redo.

| What               | Implementation                                                                           |
| ------------------ | ---------------------------------------------------------------------------------------- |
| Command processing | `QObject` subclass. Presenters call methods on it directly.                              |
| Undo/redo          | Owns a `QUndoStack`. Every mutation is wrapped in a `QUndoCommand`.                      |
| Business logic     | Calls entity methods/functions for validation or transformation before writing to Store. |

```python
class Controller(QObject):
    def __init__(self, store: Store):
        self.store = store
        self.undo_stack = QUndoStack(self)

    def create_entity(self, entity_type: str, **kwargs):
        cmd = CreateEntityCommand(self.store, entity_type, **kwargs)
        self.undo_stack.push(cmd)  # executes + records for undo

    def delete_entity(self, entity_id: str):
        cmd = DeleteEntityCommand(self.store, entity_id)
        self.undo_stack.push(cmd)
```

Each `QUndoCommand.undo()` and `redo()` modifies the Store, which emits signals,
which updates Presenters automatically. No special undo notification path needed.

**File Operations:** The Store handles .sedivis state file persistence through
`save_session(path)` and `load_session(path)` methods. Controller calls these
via QUndoCommands for consistency (though file ops may not need undo).

---

### 4. Presenters (one per panel/sidebar)

> Wires a View to the Store and Controller. Translates UI events into Controller calls.

| What         | Implementation                                                     |
| ------------ | ------------------------------------------------------------------ |
| Base class   | `QObject` (PySide6).                                               |
| Reads data   | Connects to Store signals. Reads Store directly for current state. |
| Writes data  | Calls Controller methods. Never writes to Store directly.          |
| Updates View | Calls methods on its View to refresh display.                      |

```python
class EntityListPresenter(QObject):
    def __init__(self, view: EntityListView, store: Store, controller: Controller):
        self.view = view
        self.store = store
        self.controller = controller

        # Listen to Store changes
        self.store.entity_added.connect(self._on_entity_added)
        self.store.entity_removed.connect(self._on_entity_removed)

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

---

### 5. Views (dumb widgets)

> Display only. Emit signals for user actions. Know nothing about the domain.

**Pragmatic pattern:** Views handle OS interactions (file dialogs, etc.) but emit raw inputs (`fileSelected(path)`) not domain conclusions (`createCoreAnalysis(...)`). Presenter interprets domain meaning.

| What           | Implementation                                                                                        |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| Main window    | `QMainWindow` with `QDockWidget` for each panel/sidebar.                                              |
| Panel contents | Custom `QWidget` subclasses.                                                                          |
| Lists/trees    | `QListWidget`, `QTreeWidget` (simple), or `QListView`/`QTreeView` + `QAbstractItemModel` (if needed). |
| Menus/toolbars | `QMenuBar`, `QToolBar`, `QAction`. Undo/redo actions from `QUndoStack.createUndoAction()`.            |

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
- Example: `file_panel_test.py` tests view components
- Example: `file_presenter_and_panel_test.py` tests presenter logic with views
- Helpers: Shared DRY components in `tests/helpers/`

**Test organization**: Flat structure for simplicity with descriptive filenames.

**Deferred:** Async/threading strategy and comprehensive error handling will be
added as the application grows beyond initial development.

---

## PySide6 Classes Used

| PySide6 Class                 | Where                                  | Purpose                    |
| ----------------------------- | -------------------------------------- | -------------------------- |
| `QApplication`                | App entry point                        | Event loop                 |
| `QMainWindow`                 | Root View                              | Dock areas, menus, toolbar |
| `QDockWidget`                 | Panel/Sidebar Views                    | 5 panels + 2-3 sidebars    |
| `QWidget`                     | Panel contents                         | Custom panel interiors     |
| `QListWidget` / `QTreeWidget` | Views                                  | Simple list/tree display   |
| `QUndoStack`                  | Controller                             | Undo/redo management       |
| `QUndoCommand`                | Controller                             | Each undoable action       |
| `QObject`                     | Store, Controller, Presenters          | Signals/slots              |
| `Signal` / `Slot`             | Store → Presenters, Views → Presenters | Communication              |
| `QAction`                     | Views                                  | Menu/toolbar items         |
| `QFileDialog`                 | App                                    | Open/save dialogs          |

## Self-Designed

| Component               | Size               | Notes                                                           |
| ----------------------- | ------------------ | --------------------------------------------------------------- |
| Entity classes          | ~20-50 lines each  | `dataclasses`, with `to_dict()`/`from_dict()`                   |
| Store                   | ~100-150 lines     | `QObject` + dict. Emits signals on change.                      |
| Controller              | ~100-200 lines     | Owns `QUndoStack`, calls entity logic, writes to Store.         |
| QUndoCommand subclasses | ~20-40 lines each  | One per mutation type (create, delete, update, etc.)            |
| Presenters              | ~50-100 lines each | One per panel. Wires Store ↔ View.                              |
| Session serializer      | ~50 lines          | `json.dump`/`json.load` with entity `to_dict()`/`from_dict()`.  |
| Science functions       | Various            | Domain-specific calculations in `src_legacy/science/functions/` |
| Reference data          | Static files       | Scientific reference data in `src_legacy/science/data/`         |

## Third-Party Libraries

| Library                | Purpose                    | Verdict                                               |
| ---------------------- | -------------------------- | ----------------------------------------------------- |
| `dataclasses` (stdlib) | Entity definitions         | Use.                                                  |
| `json` (stdlib)        | File save/load             | Use.                                                  |
| `uuid` (stdlib)        | Entity IDs                 | Use.                                                  |
| `pydantic`             | Validation + serialization | Optional. Useful if entities have complex validation. |
| Everything else        | —                          | Not needed at this scale.                             |

---

## Data Flow

```
User clicks delete button
  → View emits delete_requested signal (entity_id)
  → Presenter receives signal
  → Presenter calls controller.delete_entity(entity_id)
  → Controller creates DeleteEntityCommand
  → Controller pushes command onto QUndoStack (executes it)
  → Command removes entity from Store
  → Store emits entity_removed signal (entity_id)
  → All Presenters listening to entity_removed react
  → Each Presenter updates its View
```

```
User hits Ctrl+Z
  → QUndoStack.undo() calls DeleteEntityCommand.undo()
  → Command re-adds entity to Store
  → Store emits entity_added signal
  → Presenters react, Views update
```

## Key Rules

1. **Presenters never talk to each other** — they independently listen to Store signals
2. **Presenters can read the Store** — only Controller can write it
3. **Every Store write goes through QUndoCommand** — enables undo/redo
4. **Views are dumb** — they emit signals for user actions, display what Presenters tell them
5. **No custom Event Bus** — Store's Qt signals serve the same purpose
6. **No separate Domain Services layer** — entity logic lives next to entity definitions
