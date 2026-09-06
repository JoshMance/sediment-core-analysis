"""RibbonPresenter -- routes ribbon actions to AppController methods."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.ui.views.shell.ribbon.ribbon import Ribbon
from src.ui.resources.icon_provider import SedivisIconProvider
from src.ui.resources.theme import apply_theme
from src.application import AppController, ArchiveError
from src.application.workspace_state import WorkspaceState
from src.domain.entities.core_entity import CoreEntity
from src.domain.store import Store

logger = logging.getLogger(__name__)

_FILE_FILTER = "Sedivis project (*.sedivis)"


class RibbonPresenter(QObject):
    """Interprets raw button clicks from Ribbon as application actions."""

    def __init__(
        self,
        view: Ribbon,
        store: Store,
        controller: AppController,
        workspace_state: WorkspaceState | None = None,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
        self._workspace_state = workspace_state

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
        self._controller.open_core_studio()

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
            self._controller.import_core_from_image(paths[0])

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

    def _new_dataset(self) -> None:
        self._controller.create_blank_dataset()

    def _load_map(self) -> None:
        logger.info("Load Map -- not implemented yet")

    def _join_cores(self) -> None:
        from src.ui.views.shell.core_tools_dialogs import JoinCoresDialog

        JoinCoresDialog(self._view).exec()

    def _split_core(self) -> None:
        import numpy as np

        from src.ui.views.shell.core_tools_dialogs import SplitCoreDialog

        core_options = []
        for core_id, core in self._store.list_entities("CoreEntity", include_ids=True):
            if (
                isinstance(core, CoreEntity)
                and core.base_data is not None
                and (core.base_data.shape[0] > 1 or core.base_data.shape[1] > 1)
            ):
                image = self._controller.get_resolved_data(core_id)
                if image is None:
                    image = core.base_data
                data = np.ascontiguousarray(image)
                height, width = data.shape[:2]
                qimage = QImage(data.data, width, height, width * 3, QImage.Format.Format_RGB888)
                core_options.append((core_id, core.name, width, height, core.mm_per_px, QPixmap.fromImage(qimage)))
        active_core_id = self._workspace_state.active_entity_id if self._workspace_state else None
        dialog = SplitCoreDialog(core_options, self._view, preferred_core_id=active_core_id)
        dialog.splitRequested.connect(self._controller.split_core)
        dialog.exec()

    def _settings(self) -> None:
        from src.ui.views.shell.settings_dialog import SettingsDialog

        dlg = SettingsDialog(self._view)
        dlg.themeChanged.connect(self._apply_theme)
        dlg.exec()

    def _apply_theme(self, dark: bool) -> None:
        app = QApplication.instance()
        if app is None:
            return
        apply_theme(app, dark=dark)
        self._view.refresh_icons()

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
            "Join": self._join_cores,
            "Split": self._split_core,
            "Import Image": self._load_image,
            "Import Data": self._load_data,
            "New Data": self._new_dataset,
            "Settings": self._settings,
        }
