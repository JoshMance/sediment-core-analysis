"""CoreStudioPanel — column-based panel for the core creation workflow."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import QScrollArea, QToolBar, QVBoxLayout, QWidget

from src.ui.views.panels.core_studio_panel.canvas import CoreStudioCanvas
from src.ui.views.shell.variables_list import ENTITY_MIME_TYPE


class CoreStudioPanel(QWidget):
    """Panel for the Core Studio workflow.

    Layout: toolbar at top, scrollable canvas of column widgets below.
    The image column's aspect ratio governs the height of all columns —
    the panel scrolls vertically rather than distorting the image.

    Accepts entity drops only when no image has been set yet.
    """

    # Emitted when the user drops an entity onto an empty panel.
    imageDropped = Signal(str)  # entity_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._has_image = False
        self.setAcceptDrops(True)

        self.toolbar = self._build_toolbar()
        self.canvas = CoreStudioCanvas()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(scroll, 1)

    # ── Public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the core image. Height adjusts to preserve aspect ratio."""
        self._has_image = pixmap is not None and not pixmap.isNull()
        self.canvas.image_col.set_pixmap(pixmap)

    # ── Drag and drop ─────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if (
            not self._has_image
            and event.mimeData().hasFormat(ENTITY_MIME_TYPE)
        ):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        data = event.mimeData().data(ENTITY_MIME_TYPE)
        if data.isEmpty():
            event.ignore()
            return
        entity_id = bytes(data).decode("utf-8")
        event.acceptProposedAction()
        self.imageDropped.emit(entity_id)

    # ── Toolbar ───────────────────────────────────────────────

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        return tb
