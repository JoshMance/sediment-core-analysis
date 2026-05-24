"""CoreStudioPanel — column-based panel for the core creation workflow."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QToolBar, QVBoxLayout, QWidget

from src.ui.views.panels.core_studio_panel.canvas import CoreStudioCanvas
from src.ui.views.panels.core_studio_panel.columns import (
    CHANNEL_WIDTH_RATIO,
    IMAGE_WIDTH_RATIO,
    LAYER_WIDTH_RATIO,
    MAX_COLUMN_WIDTH_FRACTION,
    RULER_WIDTH_RATIO,
)
from src.ui.views.shell.variables_list import ENTITY_MIME_TYPE


class _HeaderCell(QLabel):
    """Header label with a non-layout-affecting separator line on its right edge."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIndent(0)
        self._separator = QFrame(self)
        self._separator.setProperty("role", "column-separator")
        self._separator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._separator.setGeometry(max(0, self.width() - 1), 0, 1, self.height())
        self._separator.raise_()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setPen(self.palette().color(self.foregroundRole()))
        rect = self.contentsRect().adjusted(0, -1, 0, -1)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class _CoreStudioHeader(QWidget):
    """Fixed header row aligned with the scrolling Core Studio columns."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("coreStudioHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._right_gutter = 0

        self._header_cells: list[tuple[QWidget, float]] = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(1)

        headers: list[tuple[str, float]] = [
            ("Depth", RULER_WIDTH_RATIO),
            ("Image", IMAGE_WIDTH_RATIO),
            ("Layers", LAYER_WIDTH_RATIO),
            ("R", CHANNEL_WIDTH_RATIO),
            ("G", CHANNEL_WIDTH_RATIO),
            ("B", CHANNEL_WIDTH_RATIO),
            ("L*", CHANNEL_WIDTH_RATIO),
            ("a*", CHANNEL_WIDTH_RATIO),
            ("b*", CHANNEL_WIDTH_RATIO),
        ]

        for title, ratio in headers:
            label = _HeaderCell(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(28)
            label.setProperty("role", "column-header")
            self._layout.insertWidget(self._layout.count() - 1, label)
            self._header_cells.append((label, ratio))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_max_widths()

    def set_right_gutter(self, width: int) -> None:
        """Reserve scroll-bar gutter so headers align with content columns."""
        self._right_gutter = max(0, width)
        self._layout.setContentsMargins(0, 0, self._right_gutter, 0)
        self._apply_max_widths()

    def _apply_max_widths(self) -> None:
        panel_w = self.width() - self._right_gutter
        if panel_w <= 0:
            return
        max_std = int(panel_w * MAX_COLUMN_WIDTH_FRACTION)
        for widget, ratio in self._header_cells:
            widget.setFixedWidth(int(max_std * ratio))


class CoreStudioPanel(QWidget):
    """Panel for the Core Studio workflow.

    Layout: toolbar, fixed header row, fixed air gap, then a scrollable canvas
    of column bodies below. The image column's aspect ratio governs the height
    of all columns, so the panel scrolls vertically rather than distorting the
    image.

    Accepts entity drops only when no image has been set yet.
    """

    # Emitted when the user drops an entity onto an empty panel.
    imageDropped = Signal(str)  # entity_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._has_image = False
        self.setAcceptDrops(True)

        self.toolbar = self._build_toolbar()
        self.header = _CoreStudioHeader()
        self.air_gap = QWidget()
        self.air_gap.setObjectName("coreStudioAirGap")
        self.air_gap.setFixedHeight(10)
        self.canvas = CoreStudioCanvas()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll = scroll
        self._scroll.verticalScrollBar().rangeChanged.connect(self._sync_header_gutter)
        self._scroll.verticalScrollBar().valueChanged.connect(self._sync_header_gutter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.header)
        layout.addWidget(self.air_gap)
        layout.addWidget(scroll, 1)

        self._sync_header_gutter()

    # ── Public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the core image. Height adjusts to preserve aspect ratio."""
        self._has_image = pixmap is not None and not pixmap.isNull()
        self.canvas.image_col.set_pixmap(pixmap)

    def set_channel_profiles(
        self,
        *,
        r: np.ndarray,
        g: np.ndarray,
        b: np.ndarray,
        l_star: np.ndarray,
        a_star: np.ndarray,
        b_star: np.ndarray,
    ) -> None:
        """Load channel profiles into the Core Studio data columns."""
        self.canvas.set_channel_profiles(
            r=r,
            g=g,
            b=b,
            l_star=l_star,
            a_star=a_star,
            b_star=b_star,
        )

    def clear_channel_profiles(self) -> None:
        """Clear all channel columns."""
        self.canvas.clear_channel_profiles()

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

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_header_gutter()

    def _sync_header_gutter(self, *_args: object) -> None:
        sb = self._scroll.verticalScrollBar()
        gutter = sb.width() if sb.isVisible() else 0
        self.header.set_right_gutter(gutter)
