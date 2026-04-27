"""CoreStudioPresenter — connects the Core Studio panel to Store and AppController."""
from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap

from src.application import AppController
from src.domain.entities.core_entity import CoreEntity
from src.domain.entities.image_entity import ImageEntity
from src.domain.store import Store
from src.ui.views.panels.core_studio_panel import CoreStudioPanel

logger = logging.getLogger(__name__)

_BLANK_CORE_STUDIO_ID = "core_studio_blank"


def _array_to_pixmap(data: np.ndarray) -> QPixmap:
    """Convert an (H, W, 3) uint8 RGB array to a QPixmap."""
    h, w, _ = data.shape
    bytes_per_line = 3 * w
    image = QImage(data.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image)


class CoreStudioPresenter(QObject):
    """Wires a CoreStudioPanel to the Store and AppController."""

    def __init__(
        self,
        view: CoreStudioPanel,
        store: Store,
        controller: AppController,
        core_id: str,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._core_id = core_id

        # ── View signals ──────────────────────────────────────
        self._view.imageDropped.connect(self._on_image_dropped)
        self._load_core_image()

    def _load_core_image(self) -> None:
        """Load the bound core's image into the panel."""
        if self._core_id == _BLANK_CORE_STUDIO_ID:
            return
        entity = self._store.get(self._core_id)
        if not isinstance(entity, CoreEntity):
            logger.warning("Core Studio: '%s' is not a CoreEntity", self._core_id)
            return
        if entity.data is None:
            logger.warning("Core Studio: CoreEntity '%s' has no data", self._core_id)
            return
        pixmap = _array_to_pixmap(entity.data)
        self._view.set_pixmap(pixmap)

    # ── Handlers ──────────────────────────────────────────────

    def _on_image_dropped(self, entity_id: str) -> None:
        """User dropped an image onto an empty panel — create/open a draft core."""
        entity = self._store.get(entity_id)
        if not isinstance(entity, ImageEntity):
            logger.warning("Core Studio: dropped entity '%s' is not an ImageEntity", entity_id)
            return
        if entity.data is None:
            logger.warning("Core Studio: ImageEntity '%s' has no data", entity_id)
            return
        core_id = self._controller.create_draft_core_from_image(entity_id)
        if core_id is None:
            return
        self._controller.open_core_in_studio(core_id)
