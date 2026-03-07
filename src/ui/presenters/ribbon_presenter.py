"""RibbonPresenter -- routes ribbon actions to AppController methods."""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject

from src.ui.views.shell.ribbon import Ribbon
from src.application import AppController

logger = logging.getLogger(__name__)


class RibbonPresenter(QObject):
    """Interprets raw button clicks from Ribbon as application actions."""

    def __init__(self, view: Ribbon, controller: AppController) -> None:
        super().__init__()
        self._view = view
        self._controller = controller

        self._view.buttonClicked.connect(self._on_button_clicked)

    def _on_button_clicked(self, name: str) -> None:
        handler = self._handlers.get(name)
        if handler:
            handler()
        else:
            logger.debug("No action wired for button: %s", name)

    # -- action handlers ------------------------------------------
    # Add real implementations as controller methods become available.

    def _open(self) -> None:
        logger.info("Open -- not implemented yet")

    def _save(self) -> None:
        logger.info("Save -- not implemented yet")

    def _undo(self) -> None:
        logger.info("Undo -- not implemented yet")

    def _redo(self) -> None:
        logger.info("Redo -- not implemented yet")

    def _zoom_in(self) -> None:
        logger.info("Zoom In -- not implemented yet")

    def _zoom_out(self) -> None:
        logger.info("Zoom Out -- not implemented yet")

    def _fit(self) -> None:
        logger.info("Fit -- not implemented yet")

    def _calibrate(self) -> None:
        logger.info("Calibrate -- not implemented yet")

    def _analyse(self) -> None:
        logger.info("Analyse -- not implemented yet")

    @property
    def _handlers(self) -> dict[str, object]:
        return {
            "Open": self._open,
            "Save": self._save,
            "Undo": self._undo,
            "Redo": self._redo,
            "Zoom In": self._zoom_in,
            "Zoom Out": self._zoom_out,
            "Fit": self._fit,
            "Calibrate": self._calibrate,
            "Analyse": self._analyse,
        }
