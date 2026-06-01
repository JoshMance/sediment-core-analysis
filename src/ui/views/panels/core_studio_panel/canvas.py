"""CoreStudioCanvas — lays out column widgets horizontally, image governs height."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QWidget

from src.ui.views.panels.core_studio_panel.columns import (
    MAX_COLUMN_WIDTH_FRACTION,
    RULER_WIDTH_RATIO,
    IMAGE_WIDTH_RATIO,
    LAYER_WIDTH_RATIO,
    CHANNEL_WIDTH_RATIO,
    DepthRulerColumn,
    ImageColumn,
    LayerColumn,
    DataChannelColumn,
)


class _HoverOverlay(QWidget):
    """Top-layer overlay for hover guide line and depth label."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._hover_y = -1
        self._hover_mm = -1.0
        self._depth_col_width = 0

    def set_hover(self, y: int, mm: float, depth_col_width: int) -> None:
        self._hover_y = y
        self._hover_mm = mm
        self._depth_col_width = depth_col_width
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._hover_y < 0:
            return

        painter = QPainter(self)
        painter.setPen(Qt.GlobalColor.cyan)
        painter.drawLine(0, int(self._hover_y), self.width(), int(self._hover_y))

        if self._depth_col_width <= 0:
            return

        label_text = f"{self._hover_mm:.1f} mm"
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(label_text)
        text_height = font_metrics.height()

        padding_h = 3
        padding_v = 2
        box_w = text_width + (2 * padding_h)
        box_h = text_height + (2 * padding_v)

        box_x = (self._depth_col_width - box_w) // 2
        box_y = max(0, int(self._hover_y) - box_h - 2)

        painter.fillRect(box_x, box_y, box_w, box_h, QColor(255, 255, 255))
        painter.setPen(QPen(QColor(192, 192, 192), 1))
        painter.drawRect(box_x, box_y, box_w, box_h)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(
            box_x + padding_h,
            box_y + padding_v,
            text_width,
            text_height,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            label_text,
        )


class CoreStudioCanvas(QWidget):
    """Horizontal strip of column widgets.

    Width allocation
    ~~~~~~~~~~~~~~~~
    Each column is assigned an exact width derived from its ratio constant.
    ``MAX_COLUMN_WIDTH_FRACTION`` is enforced by computing a standard column
    width on resize and applying ``setFixedWidth`` to every column. Any
    leftover horizontal space is pushed to a trailing stretch on the right.

    Height rule
    ~~~~~~~~~~~
    The ``ImageColumn`` dictates the minimum height of the entire canvas
    so that scrolling is required rather than squashing the image.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("coreStudioCanvas")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._columns: list[tuple[QWidget, float]] = []  # (widget, width_ratio)
        self._mm_per_image_px: float = 0.0
        self._hover_y = -1
        self._hover_mm = -1.0

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(1)

        self._overlay = _HoverOverlay(self)
        self._overlay.setGeometry(self.rect())
        self._overlay.raise_()

        # ── build columns in order ────────────────────────────
        self.depth_ruler = DepthRulerColumn(scale_provider=None)
        self.image_col = ImageColumn()
        self.layer_col = LayerColumn()

        self.r_col = DataChannelColumn("R")
        self.g_col = DataChannelColumn("G")
        self.b_col = DataChannelColumn("B")

        self.l_col = DataChannelColumn("L*")
        self.a_col = DataChannelColumn("a*")
        self.b_star_col = DataChannelColumn("b*")

        column_defs: list[tuple[QWidget, float]] = [
            (self.depth_ruler, RULER_WIDTH_RATIO),
            (self.image_col,   IMAGE_WIDTH_RATIO),
            (self.layer_col,   LAYER_WIDTH_RATIO),
            (self.r_col,       CHANNEL_WIDTH_RATIO),
            (self.g_col,       CHANNEL_WIDTH_RATIO),
            (self.b_col,       CHANNEL_WIDTH_RATIO),
            (self.l_col,       CHANNEL_WIDTH_RATIO),
            (self.a_col,       CHANNEL_WIDTH_RATIO),
            (self.b_star_col,  CHANNEL_WIDTH_RATIO),
        ]

        for widget, ratio in column_defs:
            self._layout.insertWidget(self._layout.count() - 1, widget)
            self._columns.append((widget, ratio))

        # Connect depth ruler hover to draw overlay
        self.depth_ruler._ruler.hoverUpdate.connect(self._on_hover_update)
        self.setMouseTracking(True)

    # ── resize handling ───────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_max_widths()
        self._sync_height()
        self._overlay.setGeometry(self.rect())
        self._overlay.raise_()
        self.depth_ruler.update()

    def _on_hover_update(self, y: int, mm: float) -> None:
        """Store hover Y and mm, trigger repaint for overlay."""
        if self._hover_y != y or self._hover_mm != mm:
            self._hover_y = y
            self._hover_mm = mm
            self._overlay.set_hover(self._hover_y, self._hover_mm, self.depth_ruler.width())

    def _apply_max_widths(self) -> None:
        """Set exact column widths from the current standard column width."""
        panel_w = self.width()
        if panel_w <= 0:
            return
        max_std = int(panel_w * MAX_COLUMN_WIDTH_FRACTION)
        for widget, ratio in self._columns:
            widget.setFixedWidth(int(max_std * ratio))

    def _sync_height(self) -> None:
        """Set canvas minimum height so the image is never squashed."""
        img_w = self.image_col.width()
        h = self.image_col.content_height_for_width(img_w)
        if h > 0:
            self.setMinimumHeight(h)
        else:
            self.setMinimumHeight(0)

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
        """Push computed channel profiles into their corresponding columns."""
        self.r_col.set_profile(r)
        self.g_col.set_profile(g)
        self.b_col.set_profile(b)
        self.l_col.set_profile(l_star)
        self.a_col.set_profile(a_star)
        self.b_star_col.set_profile(b_star)

    def clear_channel_profiles(self) -> None:
        """Clear all channel data columns."""
        for col in (
            self.r_col,
            self.g_col,
            self.b_col,
            self.l_col,
            self.a_col,
            self.b_star_col,
        ):
            col.clear_profile()

    def set_mm_per_px(self, mm_per_px: float) -> None:
        """Update the depth ruler scale. 0.0 renders the uncalibrated '?' state.

        mm_per_px is in millimetres per *image* pixel (from calibration).  The
        scale provider divides by the current display scale so the ruler draws
        in screen-pixel space, matching the on-screen image height exactly.
        """
        self._mm_per_image_px = mm_per_px

        def _scale_provider() -> float:
            if self._mm_per_image_px <= 0:
                return 0.0
            display_scale = self.image_col.display_scale()
            if display_scale <= 0:
                return 0.0
            return self._mm_per_image_px / display_scale

        self.depth_ruler.set_scale_provider(_scale_provider)
        self.depth_ruler.update()
