"""PDF export for Core Studio.

Renders the CoreStudioCanvas widget — at its full content height — to a
multi-page A4 PDF using Qt's built-in QPrinter/QPainter pipeline.

The first page includes the column header row above the canvas content.
Subsequent pages contain only canvas content.

Transform convention
--------------------
QPainter device coords are printer dots.  All canvas renders use the same
pattern: scale(s, s).translate(0, offset_in_canvas_pixels).  Qt post-
multiplies, so that order means "first translate, then scale" in terms of
which operation is applied to the point — giving device_y = (y + offset) * s.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter, QPageSize, QTransform
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QWidget

_A4 = QPageSize(QPageSize.PageSizeId.A4)


def render_to_pdf(
    canvas: QWidget,
    header: QWidget,
    path: Path,
) -> None:
    """Slice *canvas* across A4 pages and write to *path*.

    Raises:
        RuntimeError: if the QPainter cannot be opened on the printer.
    """
    canvas_w = canvas.width()
    canvas_h = canvas.height()
    if canvas_w <= 0 or canvas_h <= 0:
        return

    # Grab only the canvas-wide portion of the header.  The header widget is
    # the full panel width (including scrollbar gutter); the canvas is narrower
    # by exactly the scrollbar width.  Column widths in both are computed from
    # canvas_w, so cropping the grab to canvas_w gives perfectly aligned columns.
    header_pixmap = header.grab(QRect(0, 0, canvas_w, header.height()))

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setPageSize(_A4)
    printer.setOutputFileName(str(path))

    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel).toRect()
    page_w = page_rect.width()
    page_h = page_rect.height()

    # scale maps one canvas pixel to printer device pixels.
    scale = page_w / canvas_w

    # header_h_device: how many printer dots the header row occupies.
    header_h_device = int(header.height() * scale)

    # How many canvas pixels fit on each page.
    slice_h_first = max(1, int((page_h - header_h_device) / scale))
    slice_h_rest  = max(1, int(page_h / scale))

    painter = QPainter()
    if not painter.begin(printer):
        raise RuntimeError(f"Could not open PDF painter for '{path}'")

    # ── Page 1: header pixmap + first canvas slice ────────────────────────
    #
    # Header: draw the grabbed pixmap in raw device-pixel space so the rect
    # coordinates are unambiguously in printer dots.
    painter.setTransform(QTransform())
    painter.drawPixmap(0, 0, page_w, header_h_device, header_pixmap)

    # Canvas slice: we want canvas pixel (x, 0) → device (x*s, header_h_device).
    # With Qt post-multiply, scale(s).translate(0, h/s) gives:
    #   device_y = (canvas_y + h/s) * s = canvas_y*s + h  ✓
    # h/s = header_h_device / scale ≈ header.height()
    t = QTransform()
    t.scale(scale, scale)
    t.translate(0.0, header_h_device / scale)
    painter.setTransform(t)
    canvas.render(painter, QPoint(0, 0))

    y_canvas = slice_h_first

    # ── Remaining pages: canvas slices only ──────────────────────────────
    while y_canvas < canvas_h:
        printer.newPage()

        # We want canvas pixel (x, y_canvas) → device (x*s, 0).
        # scale(s).translate(0, -y_canvas) gives:
        #   device_y = (canvas_y - y_canvas) * s  → 0 when canvas_y == y_canvas  ✓
        t = QTransform()
        t.scale(scale, scale)
        t.translate(0.0, -float(y_canvas))
        painter.setTransform(t)
        canvas.render(painter, QPoint(0, 0))

        y_canvas += slice_h_rest

    painter.end()

