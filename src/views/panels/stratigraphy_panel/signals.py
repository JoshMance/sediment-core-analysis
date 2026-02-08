from PySide6.QtCore import QObject, Signal

class StratigraphySignals(QObject):
    """Signals for stratigraphy panel events."""
    dataChanged = Signal(object)
    selectionChanged = Signal(object)
