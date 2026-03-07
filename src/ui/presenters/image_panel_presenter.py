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

        self._load_image()
        view.selectionConfirmed.connect(self._on_selection_confirmed)

    # ── Store → View ──────────────────────────────────────────

    def _load_image(self) -> None:
        """Fetch the entity's pixel data and push a QPixmap to the view."""
        entity = self._store.get(self._entity_id)
        if entity is None or entity.data is None:
            return
        pixmap = self._ndarray_to_pixmap(entity.data)
        self._view.set_pixmap(pixmap)

    # ── View → AppController ──────────────────────────────────

    def _on_selection_confirmed(self, pixmap: QPixmap) -> None:
        """User confirmed a selection — create a CoreEntity in the Store."""
        entity = self._store.get(self._entity_id)
        base_name = getattr(entity, "name", self._entity_id)
        stem = base_name.rsplit(".", 1)[0] if "." in base_name else base_name
        core_name = f"{stem}_core"

        arr = self._pixmap_to_ndarray(pixmap)
        self._controller.create_core_entity(
            name=core_name,
            data=arr,
            source_image_id=self._entity_id,
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
