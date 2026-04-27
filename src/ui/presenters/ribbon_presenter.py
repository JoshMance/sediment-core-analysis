"""RibbonPresenter -- routes ribbon actions to AppController methods."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.ui.views.shell.ribbon.ribbon import Ribbon
from src.ui.resources.icon_provider import SedivisIconProvider
from src.application import AppController
from src.application.services.session_archive import ArchiveError

logger = logging.getLogger(__name__)

_FILE_FILTER = "Sedivis project (*.sedivis)"


class RibbonPresenter(QObject):
    """Interprets raw button clicks from Ribbon as application actions."""

    def __init__(self, view: Ribbon, controller: AppController) -> None:
        super().__init__()
        self._view = view
        self._controller = controller

        self._view.buttonClicked.connect(self._on_button_clicked)
        self._controller.ribbon_context.tabRequested.connect(self._view.set_active_tab)

    def _on_button_clicked(self, name: str) -> None:
        handler = self._handlers.get(name)
        if handler:
            handler()
        else:
            logger.debug("No action wired for button: %s", name)

    # -- session action handlers ----------------------------------

    def _new(self) -> None:
        self._controller.new_session()

    def _open(self) -> None:
        dlg = self._make_file_dialog(QFileDialog.AcceptMode.AcceptOpen)
        dlg.setDirectory(str(self._controller.recent_dirs.get("session")))
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        paths = dlg.selectedFiles()
        if not paths:
            return
        self._controller.recent_dirs.set("session", Path(paths[0]).parent)
        try:
            self._controller.load_session(Path(paths[0]))
        except ArchiveError as e:
            QMessageBox.critical(self._view, "Open Failed", str(e))

    def _save(self) -> None:
        dlg = self._make_file_dialog(QFileDialog.AcceptMode.AcceptSave)
        dlg.setDirectory(str(self._controller.recent_dirs.get("session")))
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        paths = dlg.selectedFiles()
        if not paths:
            return
        self._controller.recent_dirs.set("session", Path(paths[0]).parent)
        p = Path(paths[0].strip())
        if p.suffix.lower() != ".sedivis":
            p = p.with_suffix(".sedivis")
        try:
            self._controller.save_session(p)
        except ArchiveError as e:
            QMessageBox.critical(self._view, "Save Failed", str(e))

    def _make_file_dialog(self, mode: QFileDialog.AcceptMode) -> QFileDialog:
        """Build a non-native QFileDialog so the custom sedivis icon is shown."""
        dlg = QFileDialog(self._view)
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dlg.setIconProvider(SedivisIconProvider())
        dlg.setNameFilter(_FILE_FILTER)
        dlg.setAcceptMode(mode)
        if mode == QFileDialog.AcceptMode.AcceptOpen:
            dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
            dlg.setWindowTitle("Open Project")
        else:
            dlg.setFileMode(QFileDialog.FileMode.AnyFile)
            dlg.setWindowTitle("Save Project")
            dlg.setDefaultSuffix("sedivis")
        return dlg

    def _save_as(self) -> None:
        # Save As is identical to Save — dialog always prompts for a new path
        self._save()

    # -- other action handlers (stubs) ----------------------------

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

    def _core_studio(self) -> None:
        store = getattr(self._controller, "_store", None)
        if store is None:
            logger.warning("Core Studio: no Store available")
            return

        cores = store.list_entities(entity_type="CoreEntity", include_ids=True)
        if cores:
            latest_core_id = cores[-1][0]
            self._controller.open_core_in_studio(latest_core_id)
            return

        self._controller.open_blank_core_studio()

    def _analyse(self) -> None:
        logger.info("Analyse -- not implemented yet")

    def _load_image(self) -> None:
        dlg = QFileDialog(self._view)
        dlg.setWindowTitle("Load Image")
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Images (*.png *.jpg *.jpeg)")
        dlg.setDirectory(str(self._controller.recent_dirs.get("image")))
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        paths = dlg.selectedFiles()
        if paths:
            self._controller.recent_dirs.set("image", Path(paths[0]).parent)
            self._controller.create_image_entity(paths[0])

    def _load_data(self) -> None:
        dlg = QFileDialog(self._view)
        dlg.setWindowTitle("Load CSV Data")
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("CSV files (*.csv)")
        dlg.setDirectory(str(self._controller.recent_dirs.get("data")))
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        paths = dlg.selectedFiles()
        if paths:
            self._controller.recent_dirs.set("data", Path(paths[0]).parent)
            self._controller.create_dataset_entity(paths[0])

    def _load_map(self) -> None:
        logger.info("Load Map -- not implemented yet")

    @property
    def _handlers(self) -> dict[str, object]:
        return {
            "New": self._new,
            "Open": self._open,
            "Save": self._save,
            "Save As": self._save_as,
            "Undo": self._undo,
            "Redo": self._redo,
            "Zoom In": self._zoom_in,
            "Zoom Out": self._zoom_out,
            "Fit": self._fit,
            "Core Studio": self._core_studio,
            "Analyse": self._analyse,
            "Load Image": self._load_image,
            "Load Data": self._load_data,
            "Load Map": self._load_map,
        }
