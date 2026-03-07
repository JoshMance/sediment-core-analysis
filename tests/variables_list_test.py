"""
Isolated test for VariablesList + VariablesPresenter

Tests the view and presenter in isolation. Uses a real Store (because
the presenter needs to listen to its signals), but a stub AppController
whose delete_entity just logs — nothing actually gets removed.

Buttons let you simulate adding/removing entities so you can see:
  - Store.entityAdded signal fires → Presenter adds a row to the view
  - View.deleteRequested signal fires when Delete is clicked
  - Stub controller receives the intent (logged, not acted on)

Run with: python -m tests.variables_list_test
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from src.domain.entities.image_entity import ImageEntity
from src.ui.views.shell.variables_list import VariablesList
from src.ui.presenters.variables_presenter import VariablesPresenter
from src.domain.store import Store
from tests.helpers import LogWindow, SignalLogger


class _StubController:
    """Fake controller that logs delete calls but does nothing."""

    def __init__(self, log_window: LogWindow):
        self._log = log_window

    def delete_entity(self, entity_id: str):
        self._log.add_log(
            f"delete_entity({entity_id}) — stub, not forwarded to Store",
            source="StubCtrl",
        )


class VariablesListTest(QWidget):
    """Isolated test: VariablesList + VariablesPresenter (no real AppController)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VariablesList Test — Isolated")
        self.setGeometry(100, 100, 500, 500)

        # ── Log window ────────────────────────────
        self.log_window = LogWindow("VariablesList Logs", 520, 500)
        self.log_window.show()
        self.log_window.move(620, 100)

        # ── Store (real, so signals work) ───────────────────
        self.store = Store()

        # ── Stub controller ─────────────────────────────────
        self.stub_controller = _StubController(self.log_window)

        # ── View + Presenter ────────────────────────────────
        self.variables_list = VariablesList()
        self.presenter = VariablesPresenter(
            self.variables_list, self.store, self.stub_controller,
        )

        # ── Signal loggers ──────────────────────────
        store_logger = SignalLogger(self.log_window, "Store")
        store_logger.connect_signal(self.store.entityAdded, "entityAdded")
        store_logger.connect_signal(self.store.entityRemoved, "entityRemoved")
        self._store_logger = store_logger

        panel_logger = SignalLogger(self.log_window, "VariablesList")
        panel_logger.connect_signal(self.variables_list.deleteRequested, "deleteRequested")
        panel_logger.connect_signal(self.variables_list.entitySelected, "entitySelected")
        self._panel_logger = panel_logger

        # ── Counter for dummy entities ──────────────────────
        self._add_count = 0
        self._added_ids: list[str] = []

        # ── UI ──────────────────────────────────────────────
        layout = QVBoxLayout(self)

        self.status = QLabel("Store: 0 entities | View rows: 0")
        layout.addWidget(self.status)

        add_btn = QPushButton("Simulate: add entity to Store")
        add_btn.clicked.connect(self._on_add)
        layout.addWidget(add_btn)

        remove_btn = QPushButton("Simulate: remove last entity from Store")
        remove_btn.clicked.connect(self._on_remove)
        layout.addWidget(remove_btn)

        layout.addWidget(self.variables_list)

        self.log_window.add_log("Wired: VariablesList ↔ VariablesPresenter ↔ Store (stub AppController)")
        self.log_window.add_log("Use buttons above to simulate Store mutations")
        self.log_window.add_log("Use the Delete button in the panel to test deleteRequested")

    # ── simulate buttons ────────────────────────────────────

    def _on_add(self):
        self._add_count += 1
        entity = ImageEntity(
            name=f"test_image_{self._add_count}.png",
            file_path=Path(f"/fake/test_image_{self._add_count}.png"),
        )
        self.log_window.add_log(
            f"Adding entity: {entity.name}",
            source="Test",
        )
        eid = self.store.add(entity)
        self._added_ids.append(eid)
        self._refresh_status()

    def _on_remove(self):
        if not self._added_ids:
            self.log_window.add_log("Nothing to remove", source="Test")
            return
        eid = self._added_ids.pop()
        self.log_window.add_log(
            f"Removing entity: {eid}",
            source="Test",
        )
        self.store.remove(eid)
        self._refresh_status()

    def _refresh_status(self):
        self.status.setText(
            f"Store: {self.store.count()} entities | "
            f"View rows: {self.variables_list.row_count()}"
        )


def main():
    app = QApplication(sys.argv)
    test = VariablesListTest()
    test.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
