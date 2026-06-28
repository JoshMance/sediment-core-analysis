"""CoreImagePanelPresenter — connects a CoreImagePanel view to Store and AppController."""
from __future__ import annotations

import logging
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.core_image_panel import CoreImagePanel

logger = logging.getLogger(__name__)


class CoreImagePanelPresenter(QObject):
    """Wires a CoreImagePanel to a CoreEntity and the AppController.

    Created by WorkspacePresenter at the time the panel tab is opened.
    Lifetime is owned by WorkspacePresenter's internal dict.
    """

    def __init__(
        self,
        view: CoreImagePanel,
        store: Store,
        controller: AppController,
        entity_id: str,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._entity_id = entity_id
        self._resolved: np.ndarray | None = None

        self._load_image()
        view.cropConfirmed.connect(self._on_crop_confirmed)
        view.canvas.pixelHovered.connect(self._on_pixel_hovered)
        view.canvas.pixelLeft.connect(self._on_pixel_left)
        view.distanceCalibrated.connect(self._on_distance_calibrated)
        view.illuminantChanged.connect(self._on_illuminant_changed)
        view.filterStackChanged.connect(self._on_filter_stack_changed)
        store.entityUpdated.connect(self._on_entity_updated)

        entity = self._store.get(self._entity_id)
        if entity is not None:
            view.set_illuminant(entity.illuminant)
            view.set_filter_stack(entity.filter_stack)

    # Store -> View

    def _load_image(self) -> None:
        """Fetch the resolved display image and push it to the view."""
        resolved = self._controller.get_resolved_data(self._entity_id)
        if resolved is None:
            return
        self._resolved = resolved
        self._view.set_pixmap(self._ndarray_to_pixmap(resolved))

    # View -> AppController

    def _on_pixel_hovered(self, x: int, y: int) -> None:
        if self._resolved is None:
            return
        r, g, b = int(self._resolved[y, x, 0]), int(self._resolved[y, x, 1]), int(self._resolved[y, x, 2])
        self._controller.set_view_context(
            [f"X: {x}", f"Y: {y}", f"RGB: ({r}, {g}, {b})"]
        )

    def _on_pixel_left(self) -> None:
        self._controller.set_view_context([])

    def _on_distance_calibrated(self, mm_per_px: float) -> None:
        self._controller.set_core_mm_per_px(self._entity_id, mm_per_px)

    def _on_illuminant_changed(self, key: str | None) -> None:
        logger.debug("[illuminant] user selected %r for core %s", key, self._entity_id)
        self._controller.set_core_illuminant(self._entity_id, key)

    def _on_filter_stack_changed(self, stack: list[dict]) -> None:
        self._controller.set_filter_stack(self._entity_id, stack)

    def _on_entity_updated(self, entity_id: str, entity_type: str) -> None:
        if entity_id != self._entity_id:
            return
        entity = self._store.get(entity_id)
        if entity is not None:
            logger.debug("[core_image] entity updated %s — reloading resolved image", entity_id)
            self._view.set_illuminant(entity.illuminant)
            self._view.set_filter_stack(entity.filter_stack)
            self._load_image()

    def _on_crop_confirmed(self, x: float, y: float, w: float, h: float) -> None:
        """User confirmed a crop — create a child core from the raw base_data slice."""
        entity = self._store.get(self._entity_id)
        base_name = getattr(entity, "name", self._entity_id)
        stem = base_name.rsplit(".", 1)[0] if "." in base_name else base_name
        self._controller.create_cropped_child_core(
            parent_core_id=self._entity_id,
            x=int(x),
            y=int(y),
            w=int(w),
            h=int(h),
            name=f"{stem}_crop",
        )

    # Conversion helpers

    @staticmethod
    def _ndarray_to_pixmap(data: np.ndarray) -> QPixmap:
        h, w = data.shape[:2]
        arr = np.ascontiguousarray(data)
        qimage = QImage(arr.data, w, h, w * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)
