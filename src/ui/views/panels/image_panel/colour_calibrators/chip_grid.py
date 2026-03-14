"""MunsellChipGrid — resizable, draggable chip grid overlay on the image canvas.

The grid shape is derived from a MunsellPage:
  - columns  = the union of all chroma values across every value row, sorted
  - rows     = the value rows, in the order they appear in the page
  - a cell is only drawn where a chip actually exists on that row

Each drawn cell has a small crosshair marking the future colour-sampling point.

Aspect ratio constraint (applied during resize):
  cells must be square or portrait, up to 2× taller than wide.
  i.e.  1 ≤ cell_h/cell_w ≤ 2
  which means for the full grid: rows/cols ≤ h/w ≤ 2*rows/cols
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.science.munsell import MunsellChip, MunsellPage

_HANDLE_SIZE = 14
_MIN_CELL_PX = 10
_DEFAULT_CELL_PX = 28

_MIN_CELL_RATIO = 1.0   # square
_MAX_CELL_RATIO = 2.0   # 2× taller than wide

_CORNER_CURSORS: dict[str, Qt.CursorShape] = {
    "tl": Qt.CursorShape.SizeFDiagCursor,
    "tr": Qt.CursorShape.SizeBDiagCursor,
    "bl": Qt.CursorShape.SizeBDiagCursor,
    "br": Qt.CursorShape.SizeFDiagCursor,
}


class MunsellChipGrid(QWidget):
    """Semi-transparent chip grid overlay for a single Munsell page.

    Drag anywhere (except the bottom-right resize handle) to reposition.
    Drag the handle to resize; cell aspect ratio is clamped to [1:1, 1:2].
    """

    # Emitted when the user finishes dragging or resizing the grid.
    positionChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._rows: int = 0
        self._cols: int = 0
        # Set of (row_idx, col_idx) pairs where a chip actually exists.
        self._chip_cells: frozenset[tuple[int, int]] = frozenset()
        # Map (row_idx, col_idx) → MunsellChip — populated by set_page().
        self._cell_chips: dict[tuple[int, int], MunsellChip] = {}

        self._dragging = False
        self._resizing = False
        self._resize_corner: str | None = None
        self._drag_offset = QPoint()
        self._resize_start_global = QPoint()
        self._resize_start_pos = QPoint()
        self._resize_start_size = QSize()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.hide()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def cell_chips(self) -> dict[tuple[int, int], MunsellChip]:
        """Mapping of (row_idx, col_idx) → MunsellChip for the current page."""
        return self._cell_chips

    def set_page(self, page: MunsellPage) -> None:
        """Reconfigure the grid for the given page and reset to default size."""
        # Build sorted column list from the union of all chroma values.
        all_chromas = sorted({c.chroma for row in page.values for c in row.chromas})
        chroma_to_col = {c: i for i, c in enumerate(all_chromas)}

        self._rows = len(page.values)
        self._cols = len(all_chromas)

        # Record which (row, col) cells actually have a chip, and map to chip.
        cells: set[tuple[int, int]] = set()
        cell_chips: dict[tuple[int, int], MunsellChip] = {}
        for r, row in enumerate(page.values):
            for chip in row.chromas:
                col = chroma_to_col[chip.chroma]
                cells.add((r, col))
                cell_chips[(r, col)] = chip
        self._chip_cells = frozenset(cells)
        self._cell_chips = cell_chips

        w, h = self._clamp_size(
            self._cols * _DEFAULT_CELL_PX,
            self._rows * _DEFAULT_CELL_PX,
        )
        self.resize(w, h)
        self.update()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # noqa: ANN001
        if not self._rows or not self._cols:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gw = float(self.width())
        gh = float(self.height())
        cw = gw / self._cols
        ch = gh / self._rows

        # ── Cell fill (25% white) + 1px white borders ─────────────────────
        fill = QColor(255, 255, 255, 64)   # 25% opacity
        border = QPen(QColor("#FFFFFF"), 1)
        painter.setPen(border)
        for r, c in self._chip_cells:
            rect = QRectF(c * cw, r * ch, cw, ch)
            painter.setBrush(fill)
            painter.drawRect(rect)

        # ── Outer grid boundary (3px white) ──────────────────────────────
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(0, 0, gw, gh))

        # ── Crosshairs (2px white) ────────────────────────────────────────
        arm = min(cw, ch) * 0.15
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        for r, c in self._chip_cells:
            cx = c * cw + cw * 0.5
            cy = r * ch + ch * 0.5
            painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
            painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

        # ── Corner L-bracket handles (1px white) ──────────────────────────
        arm_h = float(_HANDLE_SIZE)
        painter.setPen(border)
        for x0, y0, dx, dy in (
            (0,  0,   arm_h,  arm_h),
            (gw, 0,  -arm_h,  arm_h),
            (0,  gh,  arm_h, -arm_h),
            (gw, gh, -arm_h, -arm_h),
        ):
            painter.drawLine(QPointF(x0, y0), QPointF(x0, y0 + dy))
            painter.drawLine(QPointF(x0, y0), QPointF(x0 + dx, y0))

    # ── Mouse interaction ─────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            for name, rect in self._corner_rects().items():
                if rect.contains(pos):
                    self._resizing = True
                    self._resize_corner = name
                    self._resize_start_global = event.globalPosition().toPoint()
                    self._resize_start_size = self.size()
                    self._resize_start_pos = self.pos()
                    self.setCursor(_CORNER_CURSORS[name])
                    event.accept()
                    return
            self._dragging = True
            self._drag_offset = pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()

        if self._resizing and self._resize_corner:
            delta = event.globalPosition().toPoint() - self._resize_start_global
            dx, dy = delta.x(), delta.y()
            corner = self._resize_corner
            sw = self._resize_start_size.width()
            sh = self._resize_start_size.height()
            sx = self._resize_start_pos.x()
            sy = self._resize_start_pos.y()

            raw_w = sw + (dx if "r" in corner else -dx)
            raw_h = sh + (dy if "b" in corner else -dy)
            cw, ch = self._clamp_size(raw_w, raw_h)

            # Keep the fixed corner in place after clamping.
            new_x = (sx + sw - cw) if "l" in corner else sx
            new_y = (sy + sh - ch) if "t" in corner else sy

            if self.parent():
                par = self.parent()
                new_x = max(0, min(new_x, par.width() - cw))
                new_y = max(0, min(new_y, par.height() - ch))

            self.move(new_x, new_y)
            self.resize(cw, ch)
            self.update()

        elif self._dragging and self.parent():
            par = self.parent()
            target = self.mapToParent(pos - self._drag_offset)
            x = max(0, min(target.x(), par.width() - self.width()))
            y = max(0, min(target.y(), par.height() - self.height()))
            self.move(x, y)
            self.raise_()

        else:
            for name, rect in self._corner_rects().items():
                if rect.contains(pos):
                    self.setCursor(_CORNER_CURSORS[name])
                    event.accept()
                    return
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            was_interacting = self._dragging or self._resizing
            self._dragging = False
            self._resizing = False
            self._resize_corner = None
            pos = event.position().toPoint()
            cursor = Qt.CursorShape.OpenHandCursor
            for name, rect in self._corner_rects().items():
                if rect.contains(pos):
                    cursor = _CORNER_CURSORS[name]
                    break
            self.setCursor(cursor)
            if was_interacting:
                self.positionChanged.emit()
        event.accept()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _corner_rects(self) -> dict[str, QRect]:
        hs = _HANDLE_SIZE
        w, h = self.width(), self.height()
        return {
            "tl": QRect(0,    0,    hs, hs),
            "tr": QRect(w-hs, 0,    hs, hs),
            "bl": QRect(0,    h-hs, hs, hs),
            "br": QRect(w-hs, h-hs, hs, hs),
        }

    def _clamp_size(self, w: int, h: int) -> tuple[int, int]:
        """Clamp (w, h) so cells stay within the allowed aspect ratio."""
        min_w = self._cols * _MIN_CELL_PX if self._cols else _MIN_CELL_PX
        min_h = self._rows * _MIN_CELL_PX if self._rows else _MIN_CELL_PX
        w = max(int(w), min_w)
        h = max(int(h), min_h)

        if self._rows and self._cols:
            ratio = h / w
            lo = (_MIN_CELL_RATIO * self._rows) / self._cols
            hi = (_MAX_CELL_RATIO * self._rows) / self._cols
            if ratio < lo:
                h = int(w * lo)
            elif ratio > hi:
                h = int(w * hi)

        return w, h
