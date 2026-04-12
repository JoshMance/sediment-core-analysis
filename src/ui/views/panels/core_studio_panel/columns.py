"""Column widgets for the Core Studio panel.

Each column is a plain QWidget with a header label and a content area.
The image column's natural height (preserving aspect ratio) governs the
height of all sibling columns via the CoreStudioCanvas layout.

Column width rule
-----------------
MAX_COLUMN_WIDTH_FRACTION defines the maximum width any single "standard"
column may occupy, expressed as a fraction of the total panel width.
Narrower columns (e.g. the depth ruler, individual R/G/B channels) are
expressed as fractions of one standard column width.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

# ── Layout constants ──────────────────────────────────────────────────────────

MAX_COLUMN_WIDTH_FRACTION = 1 / 5  # one standard column ≤ 1/5 of panel width

# Relative widths expressed as multiples of one standard column width.
RULER_WIDTH_RATIO = 1 / 3       # depth ruler is 1/3 of a standard column
IMAGE_WIDTH_RATIO = 1           # image gets one full standard column
LAYER_WIDTH_RATIO = 1           # layers get one full standard column
CHANNEL_WIDTH_RATIO = 1 / 3    # each R, G, B, L*, a*, b* channel


# ── Base column ──────────────────────────────────────────────────────────────

class _BaseColumn(QFrame):
    """A vertical strip with a header and a stretch content area."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._header = QLabel(title)
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header.setFixedHeight(28)
        self._header.setProperty("role", "column-header")
        self._layout.addWidget(self._header)

        self._content = QWidget()
        self._content.setProperty("role", "column-content")
        self._layout.addWidget(self._content, 1)


# ── Concrete columns ────────────────────────────────────────────────────────

class DepthRulerColumn(_BaseColumn):
    """Depth ruler — thin column with tick marks (rendering TBD)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Depth", parent)


class ImageColumn(_BaseColumn):
    """Core image — preserves aspect ratio at all costs.

    The image must NEVER be distorted.  The column constrains
    width to the allocated space and lets height grow to maintain
    the native aspect ratio.  The panel scrolls vertically if needed.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Image", parent)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._image_label.setScaledContents(False)
        # Replace the generic content widget with the image label.
        self._layout.removeWidget(self._content)
        self._content.deleteLater()
        self._content = self._image_label
        self._layout.addWidget(self._image_label, 1)

        self._pixmap: QPixmap | None = None

    # ── public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Display *pixmap* preserving its aspect ratio."""
        self._pixmap = pixmap
        self._apply_pixmap()

    def content_height_for_width(self, width: int) -> int:
        """Return the pixel height needed for this *width* to keep aspect ratio."""
        if self._pixmap is None or self._pixmap.isNull():
            return 0
        return int(self._pixmap.height() * (width / self._pixmap.width()))

    # ── internals ─────────────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_pixmap()

    def _apply_pixmap(self) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            self._image_label.clear()
            return
        w = self._image_label.width()
        if w <= 0:
            return
        scaled = self._pixmap.scaledToWidth(w, Qt.TransformationMode.SmoothTransformation)
        self._image_label.setPixmap(scaled)
        self._image_label.setFixedHeight(scaled.height())


class LayerColumn(_BaseColumn):
    """Layer segmentation column (rendering TBD)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Layers", parent)


class DataChannelColumn(_BaseColumn):
    """Single data-channel column (e.g. R, G, B, L*, a*, b*)."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
