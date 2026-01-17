from PySide6.QtWidgets import QWidget, QVBoxLayout
from .canvas import ImageCanvas
from .signals import ImageInteractionSignals

class ImageInteractionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Signals
        self.signals = ImageInteractionSignals()

        # Internal canvas
        self.canvas = ImageCanvas(self)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    # -------- Public API --------

    def set_image(self, pixmap):
        """Set the image to display (QPixmap)."""
        self.canvas.set_pixmap(pixmap)
        self.signals.imageChanged.emit(pixmap)

    def set_mode(self, mode):
        """Stub for interaction mode (pan, zoom, measure, etc)."""
        # Implementation handled by controller
        pass

    def clear(self):
        """Clear the canvas."""
        self.canvas.set_pixmap(None)
