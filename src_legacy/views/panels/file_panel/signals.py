from PySide6.QtCore import QObject, Signal


class FilePanelSignals(QObject):
    """Signals for file panel events."""
    fileSelected = Signal(str)  # Emitted when a file is selected (path)
    directoryChanged = Signal(str)  # Emitted when directory changes (path)
