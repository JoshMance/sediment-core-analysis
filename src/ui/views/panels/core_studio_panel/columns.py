"""Column widgets for the Core Studio panel.

Each column body is a plain QWidget with a content area only.
Titles live in the fixed header row owned by the panel; the image column's
natural height governs the height of all sibling columns via the
CoreStudioCanvas layout.

Column width rule
-----------------
MAX_COLUMN_WIDTH_FRACTION defines the maximum width any single "standard"
column may occupy, expressed as a fraction of the total panel width.
Narrower columns (e.g. the depth ruler, individual R/G/B channels) are
expressed as fractions of one standard column width.

Depth ruler rule
----------------
The depth column is mm-only for now. The ruler uses a temporary px/mm scale
constant, draws short ticks for 1 mm spacing, longer ticks for 5 mm and
10 mm spacing, and stronger landmarks at 50 mm and 100 mm. Number labels are
shown sparingly so the column stays readable at narrow widths.
"""
from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

# ── Layout constants ──────────────────────────────────────────────────────────

MAX_COLUMN_WIDTH_FRACTION = 1 / 5  # one standard column ≤ 1/5 of panel width

# Relative widths expressed as multiples of one standard column width.
RULER_WIDTH_RATIO = 1 / 3       # depth ruler is 1/3 of a standard column
IMAGE_WIDTH_RATIO = 1           # image gets one full standard column
LAYER_WIDTH_RATIO = 1           # layers get one full standard column
CHANNEL_WIDTH_RATIO = 1 / 3    # each R, G, B, L*, a*, b* channel

# Depth ruler tick constants (view-side only; will be replaced by calibration data later)
DEPTH_RULER_MINOR_MM = 1
DEPTH_RULER_MEDIUM_MM = 5
DEPTH_RULER_MAJOR_MM = 10
DEPTH_RULER_STRONG_MM = 50
DEPTH_RULER_HERO_MM = 100
DEPTH_RULER_MINOR_TICK = 8
DEPTH_RULER_MEDIUM_TICK = 13
DEPTH_RULER_MAJOR_TICK = 18
DEPTH_RULER_STRONG_TICK = 24
DEPTH_RULER_HERO_TICK = 30
DEPTH_RULER_LABEL_PAD = 4
DEPTH_RULER_LABEL_MARGIN = 4


# ── Base column ──────────────────────────────────────────────────────────────

class _BaseColumn(QFrame):
    """A vertical strip with a stretch content area."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("role", "column-body")
        self._separator = QFrame(self)
        self._separator.setProperty("role", "column-separator")
        self._separator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._content = QWidget()
        self._content.setProperty("role", "column-content")
        self._layout.addWidget(self._content, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._separator.setGeometry(max(0, self.width() - 1), 0, 1, self.height())
        self._separator.raise_()


# ── Concrete columns ────────────────────────────────────────────────────────

class _DepthRulerContent(QWidget):
    """Paint a millimeter ruler using a scale provider function.
    
    The scale provider is a callable that returns the current mm_per_px.
    The ruler calls it during paint to get fresh scale, respecting any
    changes to image geometry or calibration.
    
    Emits hoverUpdate signal when mouse enters/moves/leaves.
    """

    hoverUpdate = Signal(int, float)  # y position, mm depth value (-1, -1 for no hover)

    def __init__(self, scale_provider=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "column-content")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._scale_provider = scale_provider

    def set_scale_provider(self, provider) -> None:
        """Set the scale provider callable. Called during paint to get current mm_per_px."""
        self._scale_provider = provider
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        rect = self.contentsRect()
        if rect.isEmpty():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.fillRect(rect, self.palette().window())

        if self._scale_provider is None:
            self._draw_uncalibrated(painter, rect)
            return

        mm_per_px = self._scale_provider()
        if mm_per_px <= 0:
            self._draw_uncalibrated(painter, rect)
            return

        pixels_per_mm = 1.0 / mm_per_px
        font_metrics = QFontMetrics(self.font())
        label_interval_mm = self._label_interval_mm(pixels_per_mm, font_metrics)

        max_mm = int(math.ceil(rect.height() * mm_per_px))
        if max_mm < 0:
            return

        tick_left = rect.left() + 1
        tick_right = rect.right() - 1
        for mm in range(max_mm + 1):
            y = rect.top() + int(round(mm * pixels_per_mm))
            if y < rect.top() or y > rect.bottom():
                continue

            tick_len = self._tick_length_for_mm(mm)
            self._draw_tick(painter, tick_left, y, tick_len, side="left")
            self._draw_tick(painter, tick_right, y, tick_len, side="right")

            if label_interval_mm and mm != 0 and mm % label_interval_mm == 0:
                self._draw_label(
                    painter,
                    rect,
                    font_metrics,
                    mm,
                    y,
                    tick_len,
                    bold=mm % DEPTH_RULER_STRONG_MM == 0,
                )

    def _tick_length_for_mm(self, mm: int) -> int:
        if mm == 0 or mm % DEPTH_RULER_HERO_MM == 0:
            return DEPTH_RULER_HERO_TICK
        if mm % DEPTH_RULER_STRONG_MM == 0:
            return DEPTH_RULER_STRONG_TICK
        if mm % DEPTH_RULER_MAJOR_MM == 0:
            return DEPTH_RULER_MAJOR_TICK
        if mm % DEPTH_RULER_MEDIUM_MM == 0:
            return DEPTH_RULER_MEDIUM_TICK
        return DEPTH_RULER_MINOR_TICK

    def _label_interval_mm(self, pixels_per_mm: float, font_metrics: QFontMetrics) -> int:
        for interval in (DEPTH_RULER_MAJOR_MM, DEPTH_RULER_STRONG_MM, DEPTH_RULER_HERO_MM):
            if interval * pixels_per_mm >= font_metrics.height() + DEPTH_RULER_LABEL_MARGIN:
                return interval
        return 0

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        y = int(event.position().y())
        if self._scale_provider is None:
            self.hoverUpdate.emit(-1, -1)
            return
        
        mm_per_px = self._scale_provider()
        if mm_per_px <= 0:
            self.hoverUpdate.emit(-1, -1)
            return
        
        rect = self.contentsRect()
        mm = (y - rect.top()) * mm_per_px
        self.hoverUpdate.emit(y, mm)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hoverUpdate.emit(-1, -1)
        super().leaveEvent(event)

    def _draw_tick(self, painter: QPainter, x: int, y: int, tick_len: int, side: str) -> None:
        color = self.palette().color(self.foregroundRole())
        color.setAlphaF(0.45 if tick_len <= DEPTH_RULER_MINOR_TICK else 0.7 if tick_len <= DEPTH_RULER_MAJOR_TICK else 0.95)
        painter.setPen(color)
        if side == "left":
            painter.drawLine(x, y, x + tick_len, y)
        else:
            painter.drawLine(x - tick_len, y, x, y)

    def _draw_label(
        self,
        painter: QPainter,
        rect,
        font_metrics: QFontMetrics,
        mm: int,
        y: int,
        tick_len: int,
        *,
        bold: bool,
    ) -> None:
        label = str(mm)
        label_width = font_metrics.horizontalAdvance(label)
        text_left = rect.left() + DEPTH_RULER_LABEL_PAD
        text_right = max(text_left, rect.right() - DEPTH_RULER_LABEL_PAD)
        text_width = max(0, text_right - text_left)
        if text_width < label_width:
            return

        font = QFont(self.font())
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(self.palette().color(self.foregroundRole()))
        text_rect = painter.fontMetrics().boundingRect(label)
        text_rect.moveTo(int(text_left), int(y - text_rect.height() / 2))
        text_rect.setRight(int(text_right))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, label)

    def _draw_uncalibrated(self, painter: QPainter, rect) -> None:
        """Draw a centred '?' to indicate the ruler has not been calibrated."""
        color = self.palette().color(self.foregroundRole())
        color.setAlphaF(0.4)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "?")


class DepthRulerColumn(_BaseColumn):
    """Depth ruler — thin column with millimeter tick marks.
    
    The ruler uses a scale provider callable to get the current mm_per_px
    on each paint. This respects changes to image geometry and calibration.
    """

    def __init__(self, scale_provider=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ruler = _DepthRulerContent(scale_provider=scale_provider, parent=self._content)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.addWidget(self._ruler)

    def set_scale_provider(self, provider) -> None:
        """Update the scale provider callable."""
        self._ruler.set_scale_provider(provider)


class _PixmapContent(QWidget):
    """Paint a pixmap flush to the available width without QLabel quirks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "column-content")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._pixmap: QPixmap | None = None

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._pixmap is None or self._pixmap.isNull():
            return
        width = self.contentsRect().width()
        if width <= 0:
            return
        scaled = self._pixmap.scaledToWidth(
            width,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter = QPainter(self)
        painter.drawPixmap(0, 0, scaled)


class ImageColumn(_BaseColumn):
    """Core image — preserves aspect ratio at all costs.

    The image must NEVER be distorted.  The column constrains
    width to the allocated space and lets height grow to maintain
    the native aspect ratio.  The panel scrolls vertically if needed.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image_view = _PixmapContent()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.addWidget(self._image_view, 0, Qt.AlignmentFlag.AlignTop)
        self._content_layout.addStretch(1)

        self._pixmap: QPixmap | None = None

    # ── public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Display *pixmap* preserving its aspect ratio."""
        self._pixmap = self._normalize_pixmap(pixmap)
        self._apply_pixmap()

    def content_height_for_width(self, width: int) -> int:
        """Return the pixel height needed for this *width* to keep aspect ratio."""
        if self._pixmap is None or self._pixmap.isNull():
            return 0
        return int(self._pixmap.height() * (width / self._pixmap.width()))

    def display_scale(self) -> float:
        """Return current screen-pixels-per-image-pixel ratio (0.0 if not yet laid out)."""
        if self._pixmap is None or self._pixmap.isNull():
            return 0.0
        image_h = self._pixmap.height()
        if image_h == 0:
            return 0.0
        return self._image_view.height() / image_h

    # ── internals ─────────────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_pixmap()

    def _apply_pixmap(self) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            self._image_view.set_pixmap(None)
            self._image_view.setFixedHeight(0)
            return
        w = self._content.contentsRect().width()
        if w <= 0:
            return
        self._image_view.set_pixmap(self._pixmap)
        self._image_view.setFixedHeight(self.content_height_for_width(w))

    def _normalize_pixmap(self, pixmap: QPixmap | None) -> QPixmap | None:
        """Rotate landscape images once so the Core Studio display stays vertical."""
        if pixmap is None or pixmap.isNull():
            return None
        if pixmap.height() >= pixmap.width():
            return pixmap
        transform = QTransform().rotate(90)
        rotated = pixmap.transformed(transform, Qt.TransformationMode.FastTransformation)
        return self._trim_transparent_edges(rotated)

    def _trim_transparent_edges(self, pixmap: QPixmap) -> QPixmap:
        """Remove transparent padding left by pixmap rotation."""
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        rect = image.rect()

        left = rect.left()
        while left <= rect.right() and all(
            image.pixelColor(left, y).alpha() == 0 for y in range(rect.top(), rect.bottom() + 1)
        ):
            left += 1

        right = rect.right()
        while right >= left and all(
            image.pixelColor(right, y).alpha() == 0 for y in range(rect.top(), rect.bottom() + 1)
        ):
            right -= 1

        top = rect.top()
        while top <= rect.bottom() and all(
            image.pixelColor(x, top).alpha() == 0 for x in range(left, right + 1)
        ):
            top += 1

        bottom = rect.bottom()
        while bottom >= top and all(
            image.pixelColor(x, bottom).alpha() == 0 for x in range(left, right + 1)
        ):
            bottom -= 1

        if left > right or top > bottom:
            return pixmap
        return pixmap.copy(left, top, right - left + 1, bottom - top + 1)


class LayerColumn(_BaseColumn):
    """Layer segmentation column (rendering TBD)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)


class DataChannelColumn(_BaseColumn):
    """Single data-channel column (e.g. R, G, B, L*, a*, b*)."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._profile = _ChannelProfileContent(title=title)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.addWidget(self._profile)

    def set_profile(self, profile: np.ndarray) -> None:
        """Render a 1D profile as a vertical squiggly line plot."""
        self._profile.set_profile(profile)

    def clear_profile(self) -> None:
        """Clear profile rendering from this channel column."""
        self._profile.clear_profile()


class _ChannelProfileContent(QWidget):
    """Render a single numeric profile as a depth-aligned squiggly line plot."""

    _RANGES: dict[str, tuple[float, float]] = {
        "R": (0.0, 255.0),
        "G": (0.0, 255.0),
        "B": (0.0, 255.0),
        "L*": (0.0, 100.0),
    }

    _PENS: dict[str, tuple[int, int, int]] = {
        "R": (214, 74, 74),
        "G": (67, 160, 71),
        "B": (66, 133, 244),
        "L*": (160, 160, 160),
        "a*": (233, 30, 99),
        "b*": (255, 193, 7),
    }

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "column-content")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._title = title
        self._profile: np.ndarray | None = None

    def set_profile(self, profile: np.ndarray) -> None:
        arr = np.asarray(profile, dtype=np.float32).reshape(-1)
        self._profile = arr if arr.size else None
        self.update()

    def clear_profile(self) -> None:
        self._profile = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._profile is None:
            return
        rect = self.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        low, high = self._RANGES.get(self._title, (float(np.min(self._profile)), float(np.max(self._profile))))
        if high <= low:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            axis_color = self.palette().mid().color()
            axis_color.setAlpha(120)
            painter.setPen(axis_color)
            mid_x = rect.left() + rect.width() / 2.0
            painter.drawLine(QPointF(mid_x, rect.top()), QPointF(mid_x, rect.bottom()))

            if rect.height() == 1:
                sampled = self._profile[:1]
            else:
                src_y = np.linspace(0, self._profile.size - 1, rect.height(), dtype=np.float32)
                sampled = np.interp(src_y, np.arange(self._profile.size), self._profile)
            norm = np.clip((sampled - low) / (high - low), 0.0, 1.0)

            rgb = self._PENS.get(self._title, (230, 230, 230))
            pen_color = QColor(*rgb)
            pen_color.setAlpha(230)
            pen = QPen(pen_color, 1.5)
            painter.setPen(pen)

            x_span = max(1.0, rect.width() - 1.0)
            points = [
                QPointF(rect.left() + float(v) * x_span, rect.top() + float(i))
                for i, v in enumerate(norm)
            ]
            for i in range(1, len(points)):
                painter.drawLine(points[i - 1], points[i])
        finally:
            painter.end()


# ── Dataset plot column ──────────────────────────────────────────────────────

class _DatasetPlotContent(QWidget):
    """Render a dataset column as a depth-aligned line plot.

    ``scale_provider`` is a callable matching the depth ruler's convention:
    it returns the current mm-per-screen-pixel ratio.  A depth value ``d``
    (in mm) maps to screen y = d / scale_provider().
    """

    def __init__(self, label: str, scale_provider=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "column-content")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._label = label
        self._scale_provider = scale_provider
        self._depths: np.ndarray | None = None   # mm values
        self._values: np.ndarray | None = None   # numeric values (same length)

    def set_scale_provider(self, provider) -> None:
        self._scale_provider = provider
        self.update()

    def set_data(self, depths: np.ndarray, values: np.ndarray) -> None:
        """Load depth (mm) and value arrays. Both must be 1-D and same length."""
        arr_d = np.asarray(depths, dtype=np.float64).reshape(-1)
        arr_v = np.asarray(values, dtype=np.float64).reshape(-1)
        n = min(len(arr_d), len(arr_v))
        self._depths = arr_d[:n]
        self._values = arr_v[:n]
        self.update()

    def clear_data(self) -> None:
        self._depths = None
        self._values = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        rect = self.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            # Centre axis
            axis_color = self.palette().mid().color()
            axis_color.setAlpha(120)
            painter.setPen(axis_color)
            mid_x = rect.left() + rect.width() / 2.0
            painter.drawLine(QPointF(mid_x, rect.top()), QPointF(mid_x, rect.bottom()))

            if self._depths is None or self._values is None or self._depths.size == 0:
                return
            if self._scale_provider is None:
                return
            mm_per_screen_px = self._scale_provider()
            if mm_per_screen_px <= 0:
                return

            # Value normalisation
            finite = np.isfinite(self._values)
            if not np.any(finite):
                return
            v_min = float(np.nanmin(self._values[finite]))
            v_max = float(np.nanmax(self._values[finite]))
            span = v_max - v_min if v_max != v_min else 1.0

            pen = QPen(QColor(66, 133, 244), 1.5)
            painter.setPen(pen)

            points: list[QPointF] = []
            for d, v in zip(self._depths, self._values):
                if not (np.isfinite(d) and np.isfinite(v)):
                    continue
                screen_y = rect.top() + d / mm_per_screen_px
                norm_v = (v - v_min) / span
                screen_x = rect.left() + norm_v * (rect.width() - 1)
                points.append(QPointF(screen_x, screen_y))

            for i in range(1, len(points)):
                painter.drawLine(points[i - 1], points[i])

            # Column label (top-left, small)
            painter.setPen(self.palette().text().color())
            font = painter.font()
            font.setPointSize(max(6, font.pointSize() - 2))
            painter.setFont(font)
            painter.drawText(rect.adjusted(3, 3, -3, -3), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self._label)
        finally:
            painter.end()


class DatasetPlotColumn(_BaseColumn):
    """Column that renders a dataset variable as a depth-aligned line plot."""

    def __init__(self, label: str, scale_provider=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plot = _DatasetPlotContent(label=label, scale_provider=scale_provider)
        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._plot)

    def set_scale_provider(self, provider) -> None:
        self._plot.set_scale_provider(provider)

    def set_data(self, depths: np.ndarray, values: np.ndarray) -> None:
        self._plot.set_data(depths, values)

    def clear_data(self) -> None:
        self._plot.clear_data()
