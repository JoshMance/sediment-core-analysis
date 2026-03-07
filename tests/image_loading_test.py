"""
Image loading end-to-end test: FilePanel → FilePresenter → AppController → Store

Double-click an image file (.png, .jpg, .tif) and watch:
  1. FilePanel emits fileDoubleClicked(path)
  2. FilePresenter calls controller.create_image_entity(path)
  3. AppController loads pixels via load_image service, builds ImageEntity
  4. AppController calls store.add(entity)
  5. Store emits entityAdded(id, "ImageEntity")

Run with: python -m tests.image_loading_test
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from src.ui.views.panels.file_panel import FilePanel
from src.ui.presenters.file_presenter import FilePresenter
from src.domain.store import Store
from src.application import AppController
from tests.helpers import LogWindow, SignalLogger


class ImageLoadingTest(QWidget):
    """End-to-end image loading: View → Presenter → AppController → Store"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Loading Test")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # ── Log window ──────────────────────────────────────────
        self.log_window = LogWindow("Image Loading Logs", 520, 400)
        self.log_window.show()
        self.log_window.move(920, 100)

        # ── Build the chain ─────────────────────────────────────
        self.store = Store()
        self.controller = AppController(self.store)
        self.file_panel = FilePanel()
        self.file_presenter = FilePresenter(self.file_panel, self.store, self.controller)

        layout.addWidget(self.file_panel)

        # ── Signal loggers ──────────────────────────────────
        panel_logger = SignalLogger(self.log_window, "FilePanel")
        panel_logger.connect_signal(self.file_panel.fileDoubleClicked, "fileDoubleClicked")
        panel_logger.connect_signal(self.file_panel.pathChanged, "pathChanged")
        self._panel_logger = panel_logger  # prevent GC

        store_logger = SignalLogger(self.log_window, "Store")
        store_logger.connect_signal(self.store.entityAdded, "entityAdded")
        store_logger.connect_signal(self.store.entityUpdated, "entityUpdated")
        store_logger.connect_signal(self.store.entityRemoved, "entityRemoved")
        self._store_logger = store_logger

        # Log entity details when added
        self.store.entityAdded.connect(self._on_entity_added)

        self.log_window.add_log("Chain wired: FilePanel → FilePresenter → Controller → Store")
        self.log_window.add_log("Double-click an image file to test end-to-end loading")

    def _on_entity_added(self, entity_id: str, entity_type: str):
        entity = self.store.get(entity_id)
        shape = getattr(entity, "shape", None)
        self.log_window.add_log(
            f"Entity in store: name={entity.name}, shape={shape}",
            source="Verify",
        )
        self.log_window.add_log(
            f"Store count: {self.store.count()}",
            source="Verify",
        )


def main():
    app = QApplication(sys.argv)
    test = ImageLoadingTest()
    test.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
