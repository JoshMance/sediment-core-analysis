"""ImagePanelPresenter — connects an ImagePanel view to Store and AppController."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.image_panel import ImagePanel


class ImagePanelPresenter(QObject):
    """Wires an ImagePanel to its ImageEntity and the AppController.

    Created by WorkspacePresenter at the time the panel tab is opened.
    Lifetime is owned by WorkspacePresenter's internal dict.
    """

    def __init__(
        self,
        view: ImagePanel,
        store: Store,
        controller: AppController,
        entity_id: str,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._entity_id = entity_id
        self._data: np.ndarray | None = None

        self._load_image()
        view.cropConfirmed.connect(self._on_crop_confirmed)
        view.canvas.pixelHovered.connect(self._on_pixel_hovered)
        view.canvas.pixelLeft.connect(self._on_pixel_left)

    # ── Store → View ──────────────────────────────────────────

    def _load_image(self) -> None:
        """Fetch the entity's pixel data and push a QPixmap to the view."""
        entity = self._store.get(self._entity_id)
        if entity is None or entity.data is None:
            return
        self._data = entity.data
        pixmap = self._ndarray_to_pixmap(entity.data)
        self._view.set_pixmap(pixmap)

    # ── View → AppController ──────────────────────────────────

    def _on_pixel_hovered(self, x: int, y: int) -> None:
        if self._data is None:
            return
        r, g, b = int(self._data[y, x, 0]), int(self._data[y, x, 1]), int(self._data[y, x, 2])
        self._controller.set_view_context(
            [f"X: {x}", f"Y: {y}", f"RGB: ({r}, {g}, {b})"]
        )

    def _on_pixel_left(self) -> None:
        self._controller.set_view_context([])

    def _on_crop_confirmed(self, pixmap: QPixmap) -> None:
        """User confirmed a crop — create a cropped ImageEntity in the Store."""
        entity = self._store.get(self._entity_id)
        base_name = getattr(entity, "name", self._entity_id)
        stem = base_name.rsplit(".", 1)[0] if "." in base_name else base_name
        crop_name = f"{stem}_crop"

        arr = self._pixmap_to_ndarray(pixmap)
        self._controller.create_cropped_image(
            name=crop_name,
            data=arr,
            parent_id=self._entity_id,
        )

    # ── Conversion helpers ────────────────────────────────────

    @staticmethod
    def _ndarray_to_pixmap(data: np.ndarray) -> QPixmap:
        h, w = data.shape[:2]
        arr = np.ascontiguousarray(data)
        qimage = QImage(arr.data, w, h, w * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)

    @staticmethod
    def _pixmap_to_ndarray(pixmap: QPixmap) -> np.ndarray:
        qimage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
        w, h = qimage.width(), qimage.height()
        bytes_per_line = qimage.bytesPerLine()
        ptr = qimage.bits()
        # bytesPerLine may be wider than w*3 due to 4-byte row alignment padding.
        # Read the full strided buffer then slice out the real pixel columns.
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, bytes_per_line))
        return arr[:, : w * 3].reshape((h, w, 3)).copy()
