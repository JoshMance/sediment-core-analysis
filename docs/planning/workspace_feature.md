Summary

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
