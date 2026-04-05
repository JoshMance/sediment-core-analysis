"""ImageCanvas — pan, zoom, rotate, and crop overlay."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QPixmap, QPaintEvent, QWheelEvent, QMouseEvent,
    QPen, QColor, QPainterPath, QImage,
)
from PySide6.QtWidgets import QWidget

from src.ui.views.panels.image_panel.colour_calibrators import MunsellCalibrator, MunsellChipGrid

ZOOM_MIN = 0.1
ZOOM_MAX = 10.0
ZOOM_FACTOR = 1.1
HANDLE_SIZE = 8
HIT_TOLERANCE = 10


class ImageCanvas(QWidget):
    """Canvas widget for displaying and interacting with images.

    Supports pan (left-drag or middle-drag), scroll-wheel zoom anchored at
    cursor, rotation, and a resizable crop rectangle overlay.
    Pure view — emits signals, does no domain logic.
    """

    cropChanged = Signal(object)  # QRectF in image coordinates
    # Emitted after the calibration colour flash completes.
    # Payload: list of (rgb_tuple, MunsellChip) pairs.
    calibrationComplete = Signal(list)
    # Emitted on mouse-move when the cursor is over a valid image pixel.
    pixelHovered = Signal(int, int)  # image-space x, y
    # Emitted when the cursor leaves the image area or the canvas widget.
    pixelLeft = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._pixmap: QPixmap | None = None

        # View transforms
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._rotation = 0.0

        # Crop state (stored in image coordinates, pre-rotation)
        self._crop_rect: QRectF | None = None
        self._crop_visible = False
        self._dragging_crop: str | None = None
        self._drag_start_pos = QPoint()
        self._drag_start_rect = QRectF()

        # Pan state
        self._is_panning = False
        self._last_mouse_pos = QPoint()

        self.setMouseTracking(True)

        self._calibrator = MunsellCalibrator(parent=self)
        self._chip_grid = MunsellChipGrid(parent=self)
        self._calibration_samples: list = []
        self._calibrator.pageSelected.connect(self._on_munsell_page_selected)
        self._calibrator.confirmRequested.connect(self._on_confirm_calibration)
        self._chip_grid.positionChanged.connect(self._update_preview_colours)

    # ── Public API ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Set the image to display and reset all view state."""
        self._pixmap = pixmap
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._rotation = 0.0
        self._crop_rect = None
        self._crop_visible = False
        self.update()
        self._sync_calibrator()
        self._chip_grid.hide()

    def image_rect_in_widget(self) -> QRectF:
        """Return the rendered image bounding rect in widget-space coordinates."""
        if not self._pixmap:
            return QRectF()
        w = self._pixmap.width() * self._zoom
        h = self._pixmap.height() * self._zoom
        x = self.width() / 2 - w / 2 + self._pan_x
        y = self.height() / 2 - h / 2 + self._pan_y
        return QRectF(x, y, w, h)

    def set_calibrator_visible(self, visible: bool) -> None:
        """Show or hide the Munsell calibrator overlay."""
        if visible:
            self._sync_calibrator()
            self._calibrator.show()
        else:
            self._calibrator.hide()

    def set_rotation(self, angle: float) -> None:
        """Set rotation in degrees (display only — selection coords are unaffected)."""
        self._rotation = angle % 360
        self.update()

    def get_rotation(self) -> float:
        return self._rotation

    def set_crop_visible(self, visible: bool) -> None:
        """Show or hide the crop rectangle overlay."""
        self._crop_visible = visible
        if visible and self._crop_rect is None and self._pixmap:
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()
            self._crop_rect = QRectF(
                img_w * 0.25, img_h * 0.25, img_w * 0.5, img_h * 0.5
            )
        self.update()

    def get_crop_rect(self) -> QRectF | None:
        return self._crop_rect

    def get_crop_pixmap(self) -> QPixmap | None:
        """Crop and return the selected region from the source pixmap."""
        if not self._pixmap or not self._crop_rect:
            return None
        rect = self._crop_rect.toRect().intersected(self._pixmap.rect())
        if rect.isEmpty():
            return None
        return self._pixmap.copy(rect)

    def zoom_in(self) -> None:
        self._apply_zoom(ZOOM_FACTOR, center_on_viewport=True)

    def zoom_out(self) -> None:
        self._apply_zoom(1.0 / ZOOM_FACTOR, center_on_viewport=True)

    # ── Rendering ─────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self._pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self._pan_x, self._pan_y)
        painter.scale(self._zoom, self._zoom)

        img_x = (self.width() / self._zoom - self._pixmap.width()) / 2
        img_y = (self.height() / self._zoom - self._pixmap.height()) / 2

        # Draw image with rotation applied around its center
        painter.save()
        if self._rotation != 0:
            cx = img_x + self._pixmap.width() / 2
            cy = img_y + self._pixmap.height() / 2
            painter.translate(cx, cy)
            painter.rotate(self._rotation)
            painter.translate(-cx, -cy)
        painter.drawPixmap(int(img_x), int(img_y), self._pixmap)
        painter.restore()

        # Draw crop in unrotated image space (after restore)
        if self._crop_visible and self._crop_rect:
            painter.translate(img_x, img_y)
            self._draw_crop(painter)

    def _draw_crop(self, painter: QPainter) -> None:
        # Dimmed overlay outside the crop
        if self._pixmap:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 180))
            full_path = QPainterPath()
            full_path.addRect(QRectF(0, 0, self._pixmap.width(), self._pixmap.height()))
            sel_path = QPainterPath()
            sel_path.addRect(self._crop_rect)
            painter.drawPath(full_path.subtracted(sel_path))
            painter.restore()

        # Crop border
        painter.setPen(QPen(QColor(0, 120, 215), 2 / self._zoom))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._crop_rect)

        # Resize handles
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 120, 215))
        for handle_rect in self._get_crop_handles().values():
            painter.drawRect(handle_rect)

    # ── Mouse interaction ─────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = ZOOM_FACTOR if delta > 0 else (1.0 / ZOOM_FACTOR)
        self._apply_zoom(factor, anchor_pos=event.position().toPoint())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._crop_visible and self._crop_rect:
            img_pos = self._widget_to_image(event.position().toPoint())
            for handle_name, handle_rect in self._get_crop_handles().items():
                if handle_rect.contains(img_pos):
                    self._dragging_crop = f"resize_{handle_name}"
                    self._drag_start_pos = event.position().toPoint()
                    self._drag_start_rect = QRectF(self._crop_rect)
                    return
            if self._crop_rect.contains(img_pos):
                self._dragging_crop = "move"
                self._drag_start_pos = event.position().toPoint()
                self._drag_start_rect = QRectF(self._crop_rect)
                return

        self._is_panning = True
        self._last_mouse_pos = event.position().toPoint()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging_crop and self._crop_rect:
            img_pos = self._widget_to_image(event.position().toPoint())
            delta_widget = event.position().toPoint() - self._drag_start_pos
            delta_img = QPointF(delta_widget.x() / self._zoom, delta_widget.y() / self._zoom)

            if self._dragging_crop == "move":
                self._crop_rect.moveTo(
                    self._drag_start_rect.x() + delta_img.x(),
                    self._drag_start_rect.y() + delta_img.y(),
                )
            else:
                self._resize_crop(
                    self._dragging_crop, img_pos, self._drag_start_rect
                )

            self.cropChanged.emit(self._crop_rect)
            self.update()
            return

        if self._is_panning:
            delta = event.position().toPoint() - self._last_mouse_pos
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_mouse_pos = event.position().toPoint()
            self.update()
            self._sync_calibrator()
            return

        # Normal hover — emit image coordinates if cursor is over the image.
        img_pos = self._widget_to_image(event.position().toPoint())
        ix, iy = int(img_pos.x()), int(img_pos.y())
        if (
            self._pixmap
            and 0 <= ix < self._pixmap.width()
            and 0 <= iy < self._pixmap.height()
        ):
            self.pixelHovered.emit(ix, iy)
        else:
            self.pixelLeft.emit()

        self._update_cursor(event.position().toPoint())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self._is_panning = False
            self._dragging_crop = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        super().leaveEvent(event)
        self.pixelLeft.emit()

    # ── Internal helpers ──────────────────────────────────────

    def _apply_zoom(
        self,
        zoom_factor: float,
        center_on_viewport: bool = False,
        anchor_pos: QPoint | None = None,
    ) -> None:
        if not self._pixmap:
            return
        new_zoom = self._zoom * zoom_factor
        if not (ZOOM_MIN <= new_zoom <= ZOOM_MAX):
            return

        if center_on_viewport:
            cx, cy = self.width() / 2, self.height() / 2
            sx = (cx - self._pan_x) / self._zoom
            sy = (cy - self._pan_y) / self._zoom
            self._zoom = new_zoom
            self._pan_x = cx - sx * self._zoom
            self._pan_y = cy - sy * self._zoom
        elif anchor_pos:
            sx = (anchor_pos.x() - self._pan_x) / self._zoom
            sy = (anchor_pos.y() - self._pan_y) / self._zoom
            self._zoom = new_zoom
            self._pan_x = anchor_pos.x() - sx * self._zoom
            self._pan_y = anchor_pos.y() - sy * self._zoom
        else:
            self._zoom = new_zoom

        self.update()
        self._sync_calibrator()

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self._sync_calibrator()

    def _sync_calibrator(self) -> None:
        """Push the current canvas transform to the calibrator widget."""
        if self._calibrator.isVisible():
            self._calibrator.sync_to_canvas()

    def _on_munsell_page_selected(self, page) -> None:
        if page is None:
            self._chip_grid.hide()
        else:
            self._chip_grid.set_page(page)
            # Place at centre of canvas on first show for this page.
            self._chip_grid.move(
                max(0, (self.width() - self._chip_grid.width()) // 2),
                max(0, (self.height() - self._chip_grid.height()) // 2),
            )
            self._chip_grid.show()
            self._chip_grid.raise_()
            self._update_preview_colours()

    def _sample_current_grid(
        self,
    ) -> tuple[dict[tuple[int, int], tuple[int, int, int]], list] | None:
        """Sample 3×3 mean RGB at every crosshair. Returns (colour_map, results) or None."""
        if not self._pixmap or not self._chip_grid.isVisible():
            return None
        if not self._chip_grid.cell_chips:
            return None
        img = self._pixmap.toImage()
        cw = self._chip_grid.width() / self._chip_grid.cols
        ch_h = self._chip_grid.height() / self._chip_grid.rows
        colour_map: dict[tuple[int, int], tuple[int, int, int]] = {}
        results: list = []
        for (r, c), chip in self._chip_grid.cell_chips.items():
            wx = self._chip_grid.x() + c * cw + cw * 0.5
            wy = self._chip_grid.y() + r * ch_h + ch_h * 0.5
            img_pos = self._widget_to_image(QPoint(int(wx), int(wy)))
            rgb = self._sample_3x3(img, img_pos)
            colour_map[(r, c)] = rgb
            results.append((rgb, chip))
        return colour_map, results

    def _update_preview_colours(self) -> None:
        """Sample current grid and push colours + ratio to the calibrator mini-grid preview."""
        ratio = self._current_cell_ratio()
        result = self._sample_current_grid()
        if result is None:
            # Still update the mini grid shape even without a pixmap.
            self._calibrator.set_preview_colours({}, ratio)
            return
        colour_map, _ = result
        self._calibrator.set_preview_colours(colour_map, ratio)

    def _current_cell_ratio(self) -> float:
        """Return cell_h / cell_w for the current chip grid size."""
        if not self._chip_grid.rows or not self._chip_grid.cols:
            return 1.0
        cw = self._chip_grid.width() / self._chip_grid.cols
        ch = self._chip_grid.height() / self._chip_grid.rows
        return ch / cw if cw > 0 else 1.0

    def _on_confirm_calibration(self) -> None:
        """Sample at current grid position, store results, and emit calibrationComplete."""
        result = self._sample_current_grid()
        if result is None:
            return
        colour_map, results = result
        self._calibration_samples = results
        self._calibrator.set_preview_colours(colour_map, self._current_cell_ratio())
        print("=== Calibration samples ===")
        for rgb, chip in results:
            print(f"  RGB {rgb}  →  {chip.notation}")
        self.calibrationComplete.emit(list(results))

    def _sample_3x3(
        self, img: QImage, img_pos: QPointF
    ) -> tuple[int, int, int]:
        """Return mean RGB of the 3×3 pixel block centred on img_pos."""
        rs, gs, bs, count = 0, 0, 0, 0
        px, py = int(img_pos.x()), int(img_pos.y())
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x, y = px + dx, py + dy
                if 0 <= x < img.width() and 0 <= y < img.height():
                    c = QColor(img.pixel(x, y))
                    rs += c.red()
                    gs += c.green()
                    bs += c.blue()
                    count += 1
        if count == 0:
            return (0, 0, 0)
        return (rs // count, gs // count, bs // count)

    def _widget_to_image(self, widget_pos: QPoint) -> QPointF:
        """Convert widget-space coordinates to image-space coordinates."""
        if not self._pixmap:
            return QPointF()
        img_offset_x = (self.width() / self._zoom - self._pixmap.width()) / 2
        img_offset_y = (self.height() / self._zoom - self._pixmap.height()) / 2
        scene_x = (widget_pos.x() - self._pan_x) / self._zoom
        scene_y = (widget_pos.y() - self._pan_y) / self._zoom
        return QPointF(scene_x - img_offset_x, scene_y - img_offset_y)

    def _get_crop_handles(self) -> dict[str, QRectF]:
        if not self._crop_rect:
            return {}
        hs = HANDLE_SIZE / self._zoom
        r = self._crop_rect
        return {
            "tl": QRectF(r.left() - hs / 2, r.top() - hs / 2, hs, hs),
            "tr": QRectF(r.right() - hs / 2, r.top() - hs / 2, hs, hs),
            "bl": QRectF(r.left() - hs / 2, r.bottom() - hs / 2, hs, hs),
            "br": QRectF(r.right() - hs / 2, r.bottom() - hs / 2, hs, hs),
            "t":  QRectF(r.center().x() - hs / 2, r.top() - hs / 2, hs, hs),
            "b":  QRectF(r.center().x() - hs / 2, r.bottom() - hs / 2, hs, hs),
            "l":  QRectF(r.left() - hs / 2, r.center().y() - hs / 2, hs, hs),
            "r":  QRectF(r.right() - hs / 2, r.center().y() - hs / 2, hs, hs),
        }

    def _resize_crop(
        self, handle: str, img_pos: QPointF, start_rect: QRectF
    ) -> None:
        min_size = 10
        left, right = start_rect.left(), start_rect.right()
        top, bottom = start_rect.top(), start_rect.bottom()
        h = handle.replace("resize_", "")

        if h == "t":
            top = min(img_pos.y(), bottom - min_size)
        elif h == "b":
            bottom = max(img_pos.y(), top + min_size)
        elif h == "l":
            left = min(img_pos.x(), right - min_size)
        elif h == "r":
            right = max(img_pos.x(), left + min_size)
        elif h == "tl":
            top = min(img_pos.y(), bottom - min_size)
            left = min(img_pos.x(), right - min_size)
        elif h == "tr":
            top = min(img_pos.y(), bottom - min_size)
            right = max(img_pos.x(), left + min_size)
        elif h == "bl":
            bottom = max(img_pos.y(), top + min_size)
            left = min(img_pos.x(), right - min_size)
        elif h == "br":
            bottom = max(img_pos.y(), top + min_size)
            right = max(img_pos.x(), left + min_size)

        self._crop_rect.setCoords(left, top, right, bottom)

    def _update_cursor(self, widget_pos: QPoint) -> None:
        if self._crop_visible and self._crop_rect:
            img_pos = self._widget_to_image(widget_pos)
            for handle_name, handle_rect in self._get_crop_handles().items():
                if handle_rect.contains(img_pos):
                    if handle_name in ("tl", "br"):
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif handle_name in ("tr", "bl"):
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    elif handle_name in ("t", "b"):
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    else:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    return
            if self._crop_rect.contains(img_pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)
