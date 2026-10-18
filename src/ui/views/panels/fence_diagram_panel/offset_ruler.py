"""Offset ruler for fence diagram — bidirectional mm ruler centered at zero offset."""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget


# Offset ruler tick constants (bidirectional, centered at 0)
OFFSET_RULER_MINOR_MM = 1
OFFSET_RULER_MEDIUM_MM = 5
OFFSET_RULER_MAJOR_MM = 10
OFFSET_RULER_STRONG_MM = 50
OFFSET_RULER_HERO_MM = 100
OFFSET_RULER_MINOR_TICK = 8
OFFSET_RULER_MEDIUM_TICK = 13
OFFSET_RULER_MAJOR_TICK = 18
OFFSET_RULER_STRONG_TICK = 24
OFFSET_RULER_HERO_TICK = 30
OFFSET_RULER_LABEL_PAD = 4
OFFSET_RULER_LABEL_MARGIN = 4
OFFSET_RULER_WIDTH_RATIO = 1 / 3  # Width ratio relative to a standard column


class _OffsetRulerContent(QWidget):
    """Paint a bidirectional millimeter ruler centered at offset=0.
    
    The scale provider is a callable that returns the current mm_per_px.
    The ruler calls it during paint to get fresh scale, respecting any
    changes to image geometry or calibration.
    
    Offset increases downward (positive = down, negative = up).
    Zero offset is centered visually on the reference core.
    """

    hoverUpdate = Signal(int, float)  # y position, offset value (-1, -1 for no hover)

    def __init__(self, scale_provider=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("role", "column-content")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._scale_provider = scale_provider
        self._anchor_y = None  # Y position where offset = 0 should be drawn

    def set_anchor_y(self, anchor_y: int | None) -> None:
        """Set the Y position where offset = 0 mm is anchored."""
        self._anchor_y = anchor_y
        self.update()

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

        # Anchor point where offset = 0 mm should be drawn
        # If not set, fall back to center
        if self._anchor_y is not None:
            center_y = self._anchor_y
        else:
            center_y = rect.top() + rect.height() / 2.0
            
        max_mm = int(math.ceil(max(rect.height(), rect.top() + rect.height()) * mm_per_px))

        tick_left = rect.left() + 1
        tick_right = rect.right() - 1

        # Draw both negative (above center) and positive (below center) offsets
        # Skip minor (1mm) ticks to reduce clutter—only draw 5mm intervals and above
        for offset_mm in range(-max_mm, max_mm + 1):
            # Skip 1mm minor ticks (only show multiples of 5mm)
            if offset_mm % OFFSET_RULER_MEDIUM_MM != 0 and offset_mm != 0:
                continue
            
            # Calculate Y position: offset = 0 at center, positive down, negative up
            y = center_y + (offset_mm * pixels_per_mm)
            
            if y < rect.top() or y > rect.bottom():
                continue

            tick_len = self._tick_length_for_mm(abs(offset_mm))
            self._draw_tick(painter, tick_left, y, tick_len, side="left")
            self._draw_tick(painter, tick_right, y, tick_len, side="right")

            # Draw label for major offsets
            if label_interval_mm and offset_mm != 0 and abs(offset_mm) % label_interval_mm == 0:
                self._draw_label(
                    painter,
                    rect,
                    font_metrics,
                    offset_mm,
                    y,
                    tick_len,
                    bold=abs(offset_mm) % OFFSET_RULER_STRONG_MM == 0,
                )

    def _tick_length_for_mm(self, abs_mm: int) -> int:
        """Return tick length based on offset magnitude."""
        if abs_mm == 0 or abs_mm % OFFSET_RULER_HERO_MM == 0:
            return OFFSET_RULER_HERO_TICK
        if abs_mm % OFFSET_RULER_STRONG_MM == 0:
            return OFFSET_RULER_STRONG_TICK
        if abs_mm % OFFSET_RULER_MAJOR_MM == 0:
            return OFFSET_RULER_MAJOR_TICK
        if abs_mm % OFFSET_RULER_MEDIUM_MM == 0:
            return OFFSET_RULER_MEDIUM_TICK
        return OFFSET_RULER_MINOR_TICK

    def _label_interval_mm(self, pixels_per_mm: float, font_metrics: QFontMetrics) -> int:
        """Return label interval (major offsets to label)."""
        for interval in (OFFSET_RULER_MAJOR_MM, OFFSET_RULER_STRONG_MM, OFFSET_RULER_HERO_MM):
            if interval * pixels_per_mm >= font_metrics.height() + OFFSET_RULER_LABEL_MARGIN:
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
        center_y = rect.top() + rect.height() / 2.0
        
        # Calculate offset: center is 0, positive down, negative up
        offset_mm = (y - center_y) * mm_per_px
        self.hoverUpdate.emit(y, offset_mm)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hoverUpdate.emit(-1, -1)
        super().leaveEvent(event)

    def _draw_tick(self, painter: QPainter, x: int, y: int, tick_len: int, side: str) -> None:
        """Draw a single tick mark."""
        color = self.palette().color(self.foregroundRole())
        color.setAlphaF(0.45 if tick_len <= OFFSET_RULER_MINOR_TICK else 0.7 if tick_len <= OFFSET_RULER_MAJOR_TICK else 0.95)
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
        offset_mm: int,
        y: int,
        tick_len: int,
        *,
        bold: bool,
    ) -> None:
        """Draw offset label with proper sign."""
        # Format with +/- sign
        if offset_mm > 0:
            label = f"+{offset_mm}"
        else:
            label = f"{offset_mm}"  # Negative sign included

        label_width = font_metrics.horizontalAdvance(label)
        text_left = rect.left() + OFFSET_RULER_LABEL_PAD
        text_right = max(text_left, rect.right() - OFFSET_RULER_LABEL_PAD)
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


class OffsetRulerColumn(QFrame):
    """Offset ruler — thin column with bidirectional offset tick marks centered at zero.
    
    The ruler uses a scale provider callable to get the current mm_per_px
    on each paint. This respects changes to image geometry and calibration.
    """

    def __init__(self, scale_provider=None, parent: QWidget | None = None) -> None:
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

        self._ruler = _OffsetRulerContent(scale_provider=scale_provider, parent=self)
        self._layout.addWidget(self._ruler, 1)
        
        # Y position (in widget coords) where offset = 0 should be drawn
        self._anchor_y = None

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._separator.setGeometry(max(0, self.width() - 1), 0, 1, self.height())
        self._separator.raise_()

    def set_anchor_y(self, anchor_y: int | None) -> None:
        """Set the Y position (in widget coords) where offset = 0 mm is anchored.
        
        Args:
            anchor_y: Y pixel position where the reference core's top sits.
                     None to use center (fallback).
        """
        self._anchor_y = anchor_y
        self._ruler.set_anchor_y(anchor_y)
        self.update()

    def set_scale_provider(self, provider) -> None:
        """Set the scale provider callable."""
        self._ruler.set_scale_provider(provider)
