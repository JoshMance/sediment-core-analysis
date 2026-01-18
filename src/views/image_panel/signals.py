from PySide6.QtCore import QObject, Signal

class ImageInteractionSignals(QObject):
    imageChanged = Signal(object)
    measurementCreated = Signal(object)
    selectionChanged = Signal(object)
