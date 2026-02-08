from PySide6.QtCore import QObject, Signal


class WorkspacePanelSignals(QObject):
    """Signals for workspace panel events."""
    itemSelected = Signal(object)  # Emitted when an item is selected (WorkspaceItem)
    itemDoubleClicked = Signal(object)  # Emitted when an item is double-clicked
    itemRemoved = Signal(object)  # Emitted when an item is removed
