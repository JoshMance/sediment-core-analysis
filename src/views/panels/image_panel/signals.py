from PySide6.QtCore import QObject, Signal

class ImageInteractionSignals(QObject):
    imageChanged = Signal(object)
