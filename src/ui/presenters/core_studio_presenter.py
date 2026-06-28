"""CoreStudioPresenter — connects the Core Studio panel to Store and AppController."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFileDialog

from src.application import AppController
from src.application.services import compute_channels
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store
from src.ui.views.panels.core_studio_panel import CoreStudioPanel
from src.ui.views.panels.core_studio_panel.pdf_export import render_to_pdf

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
        self._view.exportPdfRequested.connect(self._on_export_pdf)
        self._store.entityUpdated.connect(self._on_entity_updated)
        self._load_core_image()

    def _load_core_image(self) -> None:
        """Load the bound core's resolved image into the panel."""
        core_id = self._core_id
        if core_id is None:
            self._view.clear_channel_profiles()
            return
        entity = self._store.get(core_id)
        if not isinstance(entity, CoreEntity):
            logger.warning("Core Studio: '%s' is not a CoreEntity", core_id)
            self._view.clear_channel_profiles()
            return
        resolved = self._controller.get_resolved_data(core_id)
        if resolved is None:
            logger.warning("Core Studio: CoreEntity '%s' has no image data", core_id)
            self._view.clear_channel_profiles()
            return
        pixmap = _array_to_pixmap(resolved)
        self._view.set_pixmap(pixmap)
        channels = compute_channels.for_core(resolved, entity.illuminant)
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
        """React to store changes — refresh scale and channels if our core changed."""
        if entity_id == self._core_id and entity_type == "CoreEntity":
            entity = self._store.get(entity_id)
            if isinstance(entity, CoreEntity):
                self._view.canvas.set_mm_per_px(entity.mm_per_px)
                resolved = self._controller.get_resolved_data(entity_id)
                if resolved is not None:
                    logger.debug(
                        "[illuminant] recomputing channels for core %s (illuminant=%r)",
                        entity_id, entity.illuminant,
                    )
                    channels = compute_channels.for_core(resolved, entity.illuminant)
                    logger.debug(
                        "[illuminant] L* sample (first 5 rows): %s",
                        channels.l_star[:5],
                    )
                    self._view.set_channel_profiles(
                        r=channels.r,
                        g=channels.g,
                        b=channels.b,
                        l_star=channels.l_star,
                        a_star=channels.a_star,
                        b_star=channels.b_star,
                    )
                    self._view.set_pixmap(_array_to_pixmap(resolved))

    def _on_image_dropped(self, entity_id: str) -> None:
        """User dropped an entity onto an empty panel — open if it is a core."""
        entity = self._store.get(entity_id)
        if not isinstance(entity, CoreEntity):
            logger.warning("Core Studio: dropped entity '%s' is not a CoreEntity", entity_id)
            return
        self._controller.open_core_in_studio(entity_id)

    def _on_export_pdf(self) -> None:
        """Open a save dialog and render the canvas to a PDF file."""
        if self._core_id is None:
            return  # blank panel — nothing to export
        dlg = QFileDialog(self._view)
        dlg.setWindowTitle("Export PDF")
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dlg.setFileMode(QFileDialog.FileMode.AnyFile)
        dlg.setNameFilter("PDF files (*.pdf)")
        dlg.setDefaultSuffix("pdf")
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        paths = dlg.selectedFiles()
        if not paths:
            return
        render_to_pdf(self._view.canvas, self._view.header, Path(paths[0]))
