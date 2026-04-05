Summary

> **Status:** This document was the original implementation plan for the Workspace system. The workspace system is now built. Key change from the original plan: cropping in ImagePanel now creates a child **ImageEntity** (not a CoreEntity). CoreEntity creation will be handled by the dedicated **Core Studio** panel in future work.

The workspace feature should be implemented using four components split across the application layer and the UI layer:

Application layer

WorkspaceService – receives requests (via the controller) to place entity IDs into the workspace, validates them, determines what panel type should represent them, and records this in the workspace state.

WorkspaceState – stores the logical description of what panels are currently open in the workspace and emits signals when that state changes.

UI layer

WorkspacePresenter – listens for changes in WorkspaceState. When a new workspace entry appears, it creates the appropriate panel view and its presenter and inserts the widget into the workspace view.

WorkspaceView – a simple shell view (likely a QTabWidget) that hosts the panel widgets it is told to display.

The flow is:

A presenter (e.g., the Variables presenter) asks the controller to place certain entity IDs into the workspace.

The controller delegates the request to WorkspaceService.

WorkspaceService verifies the entities exist, determines the appropriate panel type for that combination, and adds a logical entry to WorkspaceState.

WorkspaceState emits a signal describing the change.

WorkspacePresenter receives the signal, creates the panel widget and its presenter via a factory, and inserts the widget into the WorkspaceView.

WorkspaceView simply hosts the panel inside its tab container.

This keeps the workspace behaviour predictable and prevents application logic from directly manipulating UI widgets.

Goals of this design

1. Maintain clear architectural layering

Your architecture explicitly separates:

UI → Application → Domain

This design respects that boundary:

The application layer decides what panels should exist.

The UI layer decides how those panels are rendered.

No UI widgets leak into the application layer, and the UI layer does not implement application policy.

1. Keep the controller small

The controller should remain a thin orchestration point, not a place where rules accumulate.

With this structure, the controller only forwards the request:

controller.put_in_workspace(entity_ids)

All real logic lives in the service.

1. Separate logical state from UI state

The workspace is really two things:

Kind of state Owner Description
Logical workspace contents WorkspaceState which panels should exist and what entities they represent
Runtime widgets WorkspacePresenter the actual QWidget instances currently displayed

This separation is important because:

widgets are ephemeral

logical state must be serializable

session saving will rely on this state

Eventually, your .sedivis file will simply store:

the entity store

the workspace state

1. Use signals to connect layers

Instead of the service pushing UI changes directly, the application layer simply mutates state and emits signals.

That allows the UI to react naturally without tight coupling:

WorkspaceState changed
↓
WorkspacePresenter updates UI

This makes the system easier to reason about and test.

1. Prevent complexity from spreading

The biggest architectural risk in systems like this is that UI creation logic leaks everywhere.

This design avoids that by ensuring:

only one place creates panel widgets: WorkspacePresenter

only one place decides what panel type is appropriate: WorkspaceService

only one place stores what is open: WorkspaceState

Each component has a single responsibility.

Why the presenter creates widgets

The presenter sits at the boundary between application state and UI.

It already exists to translate between:

domain/application data

visual components

Creating panels here keeps UI construction close to where UI logic already lives, while still leaving application policy outside the UI.

Result

This design gives you:

dynamic runtime panel creation

simple application logic

clean layering

a natural path to session saving

minimal moving parts

And most importantly, it stays small and understandable, which matches your goal of preventing the architecture from becoming overly complicated.

---

# Plan: Workspace + ImagePanel

## TL;DR

Add the full Workspace system (WorkspaceState + WorkspaceService in application layer, WorkspaceView in shell/, WorkspacePresenter in ui/presenters/) and the first runtime panel (ImagePanel in panels/) that displays an image, allows pan/zoom/rotate/crop, and creates a child ImageEntity on confirm. Double-clicking an entity in VariablesList triggers the flow.

---

## Phase 1 — Application layer (WorkspaceState + WorkspaceService)

**New: `src/application/workspace_state.py`**

- `WorkspaceEntry` dataclass: `entity_id: str`, `panel_type: str`
- `WorkspaceState(QObject)`: signals `panelAdded(object)` (WorkspaceEntry), `panelRemoved(str)` (entity_id), `panelFocusRequested(str)` (entity_id)
- Public: `open(entry)` — emits `panelAdded` or `panelFocusRequested` if already open; `close(entity_id)` — emits `panelRemoved`; `is_open(entity_id) -> bool`

**New: `src/application/services/workspace_service.py`**

- Stateless function `open_entity(entity_id, store, workspace_state)`: validates entity exists, maps entity type → panel type via `_PANEL_TYPE_MAP = {"ImageEntity": "ImagePanel"}`, calls `workspace_state.open(entry)`

**Modify: `src/application/app_controller.py`**

- Accept `workspace_state: WorkspaceState` in `__init__` (alongside store)
- Add `open_in_workspace(entity_id: str) -> None` — calls `workspace_service.open_entity(...)`

---

## Phase 2 — VariablesList double-click signal

**Modify: `src/ui/views/shell/variables_list.py`**

- Add `entityOpenRequested = Signal(str)` — fires entity_id on QTreeWidget `itemDoubleClicked`

**Modify: `src/ui/presenters/variables_presenter.py`**

- Connect `view.entityOpenRequested` → `controller.open_in_workspace`

---

## Phase 3 — ImagePanel view (parallel with Phase 1)

**New: `src/ui/views/panels/image_panel/__init__.py`** — exports `ImagePanel`

**New: `src/ui/views/panels/image_panel/canvas.py`** — `ImageCanvas(QWidget)`

- Port from `src_legacy/views/panels/image_panel/canvas.py`
- REMOVE: all calibration state/mode/drawing (`_calib_*`, `MODE_CALIBRATE`, `_draw_calibration`, `_widget_to_rotated_image`)
- KEEP: pan, zoom (wheel + zoom_in/zoom_out methods), rotation, crop rectangle with resize handles
- KEEP: `crop_changed = Signal(object)` (QRectF in image coords)
- No inline styles (`setStyleSheet` calls)

**New: `src/ui/views/panels/image_panel/image_panel.py`** — `ImagePanel(QWidget)`

- Port from `src_legacy/views/panels/image_panel/widget.py`
- REMOVE: calibration toolbar buttons, calib_input_widget, on_selection_confirmed/on_calibration_confirmed callbacks, preview_label with inline style
- ADD: `cropConfirmed = Signal(object)` emitted with `QPixmap` of crop when user clicks Confirm
- Toolbar: zoom in, zoom out, rotation slider + label, separator, Crop (checkable), separator, Confirm + Cancel (hidden until Crop active)
- Public: `set_pixmap(pixmap: QPixmap | None)`, `get_selection_pixmap() -> QPixmap | None`
- No inline `setStyleSheet` calls anywhere; button sizing (`setFixedSize`) is acceptable

---

## Phase 4 — ImagePanelPresenter (depends on Phase 1 + Phase 3)

**New: `src/ui/presenters/image_panel_presenter.py`** — `ImagePanelPresenter`

- `__init__(self, view: ImagePanel, store: Store, controller: AppController, entity_id: str)`
- On init: fetches `ImageEntity` from store, converts `entity.data` (NDArray uint8 RGB) to `QPixmap`, calls `view.set_pixmap(pixmap)`
- Connects `view.cropConfirmed` → `_on_crop_confirmed(pixmap)`
- `_on_crop_confirmed`: converts QPixmap → numpy array (via QImage.Format_RGB888), calls `controller.create_cropped_image(name=f"{entity_name}_crop", data=arr, parent_id=entity_id)`

---

## Phase 5 — WorkspaceView (parallel with Phase 3)

**New: `src/ui/views/shell/workspace_view.py`** — `WorkspaceView(QWidget)`

- Wraps `QTabWidget` with `setTabsClosable(True)`, `tabCloseRequested` signal
- Public: `add_tab(widget, title, entity_id)` — stores `entity_id → tab_index` mapping; `remove_tab(entity_id)`; `focus_tab(entity_id)`
- Emits `tabClosed = Signal(str)` (entity_id) when user closes a tab

---

## Phase 6 — WorkspacePresenter (depends on Phases 1, 3, 4, 5)

**New: `src/ui/presenters/workspace_presenter.py`** — `WorkspacePresenter`

- `__init__(self, view: WorkspaceView, workspace_state: WorkspaceState, store: Store, controller: AppController)`
- Connects: `workspace_state.panelAdded` → `_on_panel_added`; `workspace_state.panelFocusRequested` → `view.focus_tab`; `view.tabClosed` → `workspace_state.close`
- `_on_panel_added(entry)`: looks up `_PANEL_FACTORIES[entry.panel_type]`, calls factory → (panel_view, panel_presenter), stores both (to prevent GC), calls `view.add_tab(panel_view, entity_name, entry.entity_id)`
- Panel factory registry (module-level dict): `{"ImagePanel": _make_image_panel}`; factory callable signature: `(entry, store, controller) -> (QWidget, object)`
- Keeps `dict[entity_id → (panel_view, panel_presenter)]` to maintain lifetime

---

## Phase 7 — Wire up main.py (depends on all phases)

- Create `workspace_state = WorkspaceState()` (alongside `store`)
- Pass `workspace_state=workspace_state` to `AppController`
- Create `workspace_view = WorkspaceView()` in views section
- Create `workspace_presenter = WorkspacePresenter(workspace_view, workspace_state, store, controller)`
- Update layout: replace empty `QWidget()` stretch=3 center with `workspace_view`

---

## Phase 8 — Manual test

**New: `tests/workspace_test.py`** — end-to-end test: load image, double-click in VariablesList, check workspace opens tab, draw crop, confirm, check child ImageEntity appears in VariablesList

---

## Relevant files

- `src/application/app_controller.py` — add workspace_state + open_in_workspace
- `src/application/workspace_state.py` — NEW
- `src/application/services/workspace_service.py` — NEW
- `src/ui/views/shell/workspace_view.py` — NEW (shell, always present)
- `src/ui/views/shell/variables_list.py` — add entityOpenRequested signal
- `src/ui/presenters/variables_presenter.py` — connect entityOpenRequested
- `src/ui/views/panels/image_panel/` — NEW (3 files)
- `src/ui/presenters/workspace_presenter.py` — NEW
- `src/ui/presenters/image_panel_presenter.py` — NEW
- `main.py` — wire workspace_state, workspace_view, workspace_presenter; update layout
- Reference: `src_legacy/views/panels/image_panel/canvas.py` (port base)
- Reference: `src_legacy/views/panels/image_panel/widget.py` (port base)

## Verification

1. `uv run python -m tests.workspace_test` — visual end-to-end
2. `uv run python -m tests.container_test` — regression (no regressions)
3. `uv run python main.py --light` — run app, double-click loaded image, confirm crop, check VariablesList shows new child ImageEntity

## Decisions

- Double-click in VariablesList opens workspace tab
- Tab title = entity name
- If entity already open: focus existing tab, no duplicate
- No calibration in this iteration — CalibrationMode stripped entirely from canvas
- No inline setStyleSheet in any new file; button sizing (setFixedSize) is acceptable
- WorkspaceState created at root in main.py (same pattern as Store) and passed to AppController
- Panel view + presenter lifetime owned by WorkspacePresenter's dict
