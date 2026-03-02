"""
Full integration test: FilePanel + WorkspacePanel with Controller and Store

Load images via FilePanel, see them appear in WorkspacePanel, delete them
from WorkspacePanel. Detailed logging shows every signal, method call,
and Store state change along the way.

Load chain:
  FilePanel.fileDoubleClicked → FilePresenter._on_file_selected
    → Controller.create_image_entity → Store.add → Store.entityAdded
    → WorkspacePresenter._on_entity_added → WorkspacePanel.add_row

Delete chain:
  WorkspacePanel.deleteRequested → WorkspacePresenter._on_delete_requested
    → Controller.delete_entity → Store.remove → Store.entityRemoved
    → WorkspacePresenter._on_entity_removed → WorkspacePanel.remove_row

Run with: python -m src.tests.workspace_test
"""
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSplitter, QLabel, QGroupBox,
)
from PySide6.QtCore import Qt

from src.views.panels.file_panel import FilePanel
from src.views.panels.workspace_panel import WorkspacePanel
from src.presenters.file_presenter import FilePresenter
from src.presenters.workspace_presenter import WorkspacePresenter
from src.store import Store
from src.controller import Controller
from src.tests.helpers import LogWindow, SignalLogger


class WorkspaceTest(QWidget):
    """Full integration: load images + manage them in workspace."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workspace Test — Full Integration")
        self.setGeometry(100, 100, 900, 650)

        # ── Log window ──────────────────────────────────────
        self.log_window = LogWindow("Integration Logs", 580, 650)
        self.log_window.show()
        self.log_window.move(1020, 100)

        # ── Core components ─────────────────────────────────
        self.store = Store()
        self.controller = Controller(self.store)

        # ── Views ───────────────────────────────────────────
        self.file_panel = FilePanel()
        self.workspace_panel = WorkspacePanel()

        # ── Presenters ──────────────────────────────────────
        self.file_presenter = FilePresenter(
            self.file_panel, self.store, self.controller,
        )
        self.workspace_presenter = WorkspacePresenter(
            self.workspace_panel, self.store, self.controller,
        )

        # ── Signal loggers ──────────────────────────────────
        self._setup_loggers()

        # ── Detailed trace hooks ────────────────────────────
        self._setup_trace_hooks()

        # ── Layout ──────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        file_group = QGroupBox("File Panel")
        file_layout = QVBoxLayout()
        file_layout.addWidget(self.file_panel)
        file_group.setLayout(file_layout)

        workspace_group = QGroupBox("Workspace Panel")
        workspace_layout = QVBoxLayout()
        self.status_label = QLabel("Store: 0 entities")
        workspace_layout.addWidget(self.status_label)
        workspace_layout.addWidget(self.workspace_panel)
        workspace_group.setLayout(workspace_layout)

        splitter.addWidget(file_group)
        splitter.addWidget(workspace_group)
        splitter.setSizes([500, 400])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self.log_window.add_log("═══ Integration test ready ═══")
        self.log_window.add_log("Chain: FilePanel → FilePresenter → Controller → Store → WorkspacePresenter → WorkspacePanel")
        self.log_window.add_log("Double-click an image to load it. Select + Delete to remove it.")
        self.log_window.add_log("")

    def _setup_loggers(self):
        """Connect all signals to the log window with source labels."""
        # FilePanel signals
        fp_logger = SignalLogger(self.log_window, "FilePanel")
        fp_logger.connect_signal(self.file_panel.fileDoubleClicked, "fileDoubleClicked")
        fp_logger.connect_signal(self.file_panel.pathChanged, "pathChanged")
        self._fp_logger = fp_logger

        # WorkspacePanel signals
        wp_logger = SignalLogger(self.log_window, "WorkspacePanel")
        wp_logger.connect_signal(self.workspace_panel.deleteRequested, "deleteRequested")
        wp_logger.connect_signal(self.workspace_panel.entitySelected, "entitySelected")
        self._wp_logger = wp_logger

        # Store signals
        store_logger = SignalLogger(self.log_window, "Store")
        store_logger.connect_signal(self.store.entityAdded, "entityAdded")
        store_logger.connect_signal(self.store.entityRemoved, "entityRemoved")
        store_logger.connect_signal(self.store.entityUpdated, "entityUpdated")
        self._store_logger = store_logger

    def _setup_trace_hooks(self):
        """Add detailed trace logging for presenter and controller methods."""

        # ── FilePresenter trace ─────────────────────────────
        original_file_selected = self.file_presenter._on_file_selected

        def traced_file_selected(file_path: str):
            self.log_window.add_log(
                f"_on_file_selected({file_path})",
                source="FilePresenter",
            )
            original_file_selected(file_path)

        self.file_presenter._on_file_selected = traced_file_selected

        # ── Controller trace ────────────────────────────────
        original_create = self.controller.create_image_entity
        original_delete = self.controller.delete_entity

        def traced_create(file_path: str):
            self.log_window.add_log(
                f"create_image_entity({file_path})",
                source="Controller",
            )
            result = original_create(file_path)
            self.log_window.add_log(
                f"  → entity added with id={result}",
                source="Controller",
            )
            return result

        def traced_delete(entity_id: str):
            entity = self.store.get(entity_id)
            name = getattr(entity, "name", "?") if entity else "?"
            self.log_window.add_log(
                f"delete_entity({entity_id}) — name={name}",
                source="Controller",
            )
            result = original_delete(entity_id)
            self.log_window.add_log(
                f"  → entity removed",
                source="Controller",
            )
            return result

        self.controller.create_image_entity = traced_create
        self.controller.delete_entity = traced_delete

        # ── WorkspacePresenter trace ────────────────────────
        original_on_added = self.workspace_presenter._on_entity_added
        original_on_removed = self.workspace_presenter._on_entity_removed
        original_on_delete_req = self.workspace_presenter._on_delete_requested

        def traced_on_added(entity_id: str, entity_type: str):
            self.log_window.add_log(
                f"_on_entity_added({entity_id}, {entity_type}) — adding row to view",
                source="WkspPresenter",
            )
            original_on_added(entity_id, entity_type)
            self._refresh_status()

        def traced_on_removed(entity_id: str, entity_type: str):
            self.log_window.add_log(
                f"_on_entity_removed({entity_id}, {entity_type}) — removing row from view",
                source="WkspPresenter",
            )
            original_on_removed(entity_id, entity_type)
            self._refresh_status()

        def traced_on_delete_req(entity_id: str):
            self.log_window.add_log(
                f"_on_delete_requested({entity_id}) — routing to Controller",
                source="WkspPresenter",
            )
            original_on_delete_req(entity_id)

        self.workspace_presenter._on_entity_added = traced_on_added
        self.workspace_presenter._on_entity_removed = traced_on_removed
        self.workspace_presenter._on_delete_requested = traced_on_delete_req

        # ── Store state dump after every mutation ───────────
        self.store.entityAdded.connect(self._dump_store_state)
        self.store.entityRemoved.connect(self._dump_store_state)

    def _dump_store_state(self, *_args):
        """Print current Store contents to log."""
        count = self.store.count()
        summary = self.store.summary()
        self.log_window.add_log(
            f"Store state: {count} entities — {summary}",
            source="Verify",
        )
        entities = self.store.list_entities(include_ids=True)
        for eid, entity in entities:
            name = getattr(entity, "name", "?")
            self.log_window.add_log(f"  {eid}: {name}", source="Verify")
        self.log_window.add_log("")  # blank line separator

    def _refresh_status(self):
        self.status_label.setText(
            f"Store: {self.store.count()} entities | "
            f"View rows: {self.workspace_panel.row_count()}"
        )


def main():
    app = QApplication(sys.argv)
    test = WorkspaceTest()
    test.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
