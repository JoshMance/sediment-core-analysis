"""CoreStudioCanvas — lays out column widgets horizontally, image governs height."""
from __future__ import annotations

from PySide6.QtCore import Qt
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


class CoreStudioCanvas(QWidget):
    """Horizontal strip of column widgets.

    Width allocation
    ~~~~~~~~~~~~~~~~
    Each column is assigned a stretch factor proportional to its width
    ratio constant.  ``MAX_COLUMN_WIDTH_FRACTION`` is enforced by
    ``setMaximumWidth`` on each column whenever the canvas resizes.

    Height rule
    ~~~~~~~~~~~
    The ``ImageColumn`` dictates the minimum height of the entire canvas
    so that scrolling is required rather than squashing the image.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._columns: list[tuple[QWidget, float]] = []  # (widget, width_ratio)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        # ── build columns in order ────────────────────────────
        self.depth_ruler = DepthRulerColumn()
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

        # Stretch factors — multiply by 300 to get integer-friendly values.
        for widget, ratio in column_defs:
            stretch = int(ratio * 300)
            layout.addWidget(widget, stretch)
            self._columns.append((widget, ratio))

    # ── resize handling ───────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_max_widths()
        self._sync_height()

    def _apply_max_widths(self) -> None:
        """Cap each column at MAX_COLUMN_WIDTH_FRACTION of the canvas width."""
        panel_w = self.width()
        if panel_w <= 0:
            return
        max_std = int(panel_w * MAX_COLUMN_WIDTH_FRACTION)
        for widget, ratio in self._columns:
            widget.setMaximumWidth(int(max_std * ratio))

    def _sync_height(self) -> None:
        """Set canvas minimum height so the image is never squashed."""
        img_w = self.image_col.width()
        h = self.image_col.content_height_for_width(img_w)
        if h > 0:
            header_h = 28  # matches column header fixed height
            self.setMinimumHeight(h + header_h)
        else:
            self.setMinimumHeight(0)
