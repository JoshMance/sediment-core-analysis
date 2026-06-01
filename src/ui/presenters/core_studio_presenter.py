"""CoreStudioPresenter — connects the Core Studio panel to Store and AppController."""
from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap

from src.application import AppController
from src.application.services import compute_channels
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store
from src.ui.views.panels.core_studio_panel import CoreStudioPanel

logger = logging.getLogger(__name__)


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
        core_id: str | None,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._core_id = core_id

        # ── View signals ──────────────────────────────────────
        self._view.imageDropped.connect(self._on_image_dropped)
        self._store.entityUpdated.connect(self._on_entity_updated)
        self._load_core_image()

    def _load_core_image(self) -> None:
        """Load the bound core's image into the panel."""
        core_id = self._core_id
        if core_id is None:
            self._view.clear_channel_profiles()
            return
        entity = self._store.get(core_id)
        if not isinstance(entity, CoreEntity):
            logger.warning("Core Studio: '%s' is not a CoreEntity", core_id)
            self._view.clear_channel_profiles()
            return
        if entity.data is None:
            logger.warning("Core Studio: CoreEntity '%s' has no data", core_id)
            self._view.clear_channel_profiles()
            return
        pixmap = _array_to_pixmap(entity.data)
        self._view.set_pixmap(pixmap)
        channels = compute_channels.for_core(entity.data)
        self._view.set_channel_profiles(
            r=channels.r,
            g=channels.g,
            b=channels.b,
            l_star=channels.l_star,
            a_star=channels.a_star,
            b_star=channels.b_star,
        )
        self._view.canvas.set_mm_per_px(entity.mm_per_px)

    # ── Handlers ──────────────────────────────────────────────

    def _on_entity_updated(self, entity_id: str, entity_type: str) -> None:
        """React to store changes — refresh the depth ruler scale if our core changed."""
        if entity_id == self._core_id and entity_type == "CoreEntity":
            entity = self._store.get(entity_id)
            if isinstance(entity, CoreEntity):
                self._view.canvas.set_mm_per_px(entity.mm_per_px)

    def _on_image_dropped(self, entity_id: str) -> None:
        """User dropped an entity onto an empty panel — open if it is a core."""
        entity = self._store.get(entity_id)
        if not isinstance(entity, CoreEntity):
            logger.warning("Core Studio: dropped entity '%s' is not a CoreEntity", entity_id)
            return
        self._controller.open_core_in_studio(entity_id)
