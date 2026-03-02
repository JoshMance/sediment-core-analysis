"""
Manual test for Store — QObject facade with signals

Exercises Store CRUD and verifies that signals fire correctly.
Uses LogWindow + SignalLogger for visual signal monitoring.

Run with: python -m src.tests.store_test
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from src.entities.image_entity import ImageEntity
from src.store import Store
from src.tests.helpers import LogWindow, SignalLogger


class StoreTest(QWidget):
    """Interactive test harness for Store signals and CRUD."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Store Test")
        self.setGeometry(100, 100, 360, 400)

        # ── Store ───────────────────────────────────────────
        self.store = Store()

        # ── Log window ──────────────────────────────────────
        self.log_window = LogWindow("Store Signal Logs", 500, 400)
        self.log_window.show()
        self.log_window.move(500, 100)

        # ── Signal logger ───────────────────────────────────
        self.signal_logger = SignalLogger(self.log_window, "Store")
        self.signal_logger.connect_signal(self.store.entityAdded, "entityAdded")
        self.signal_logger.connect_signal(self.store.entityRemoved, "entityRemoved")
        self.signal_logger.connect_signal(self.store.entityUpdated, "entityUpdated")

        # ── Track ids for later operations ──────────────────
        self._added_ids: list[str] = []
        self._update_count: int = 0

        # ── UI ──────────────────────────────────────────────
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.status_label = QLabel("Store: 0 entities")
        layout.addWidget(self.status_label)

        buttons = [
            ("Add ImageEntity", self._on_add),
            ("Update last name", self._on_update),
            ("Remove last", self._on_remove),
            ("Get last", self._on_get),
            ("List all", self._on_list),
            ("Summary", self._on_summary),
            ("Clear", self._on_clear),
            ("Run auto-sequence", self._on_auto),
        ]
        for label, slot in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        self.log_window.add_log("Store test ready — click buttons or run auto-sequence")

    # ── helpers ─────────────────────────────────────────────

    def _refresh_status(self):
        self.status_label.setText(f"Store: {self.store.count()} entities")

    def _log(self, msg: str):
        self.log_window.add_log(msg)

    # ── button slots ────────────────────────────────────────

    def _on_add(self):
        n = len(self._added_ids) + 1
        img = ImageEntity(name=f"image_{n}.png", file_path=Path(f"/data/image_{n}.png"))
        eid = self.store.add(img)
        self._added_ids.append(eid)
        self._log(f"Added → id={eid}")
        self._refresh_status()

    def _on_update(self):
        if not self._added_ids:
            self._log("Nothing to update")
            return
        eid = self._added_ids[-1]
        self._update_count += 1
        new_name = f"renamed_{self._update_count}.png"
        self.store.update_field(eid, "name", new_name)
        self._log(f"Updated {eid} name → {new_name}")
        self._refresh_status()

    def _on_remove(self):
        if not self._added_ids:
            self._log("Nothing to remove")
            return
        eid = self._added_ids.pop()
        removed = self.store.remove(eid)
        self._log(f"Removed → {removed.name} (id={eid})")
        self._refresh_status()

    def _on_get(self):
        if not self._added_ids:
            self._log("Nothing to get")
            return
        eid = self._added_ids[-1]
        entity = self.store.get(eid)
        self._log(f"Get {eid} → {entity}")

    def _on_list(self):
        entities = self.store.list_entities(include_ids=True)
        if not entities:
            self._log("Store is empty")
            return
        for eid, e in entities:
            self._log(f"  {eid}: {e.name}")

    def _on_summary(self):
        self._log(f"Summary: {self.store.summary()}")
        self._log(f"Total count: {self.store.count()}")

    def _on_clear(self):
        self.store.clear()
        self._added_ids.clear()
        self._log("Cleared store")
        self._refresh_status()

    def _on_auto(self):
        """Run a scripted add → update → remove sequence."""
        self._log("── Auto-sequence start ──")

        # Add three
        ids = []
        for i in range(1, 4):
            img = ImageEntity(name=f"auto_{i}.png")
            eid = self.store.add(img)
            ids.append(eid)
            self._log(f"  add auto_{i} → {eid}")

        self._log(f"  count = {self.store.count()}")
        self._log(f"  summary = {self.store.summary()}")

        # Update second
        self.store.update_field(ids[1], "name", "updated_auto_2.png")
        self._log(f"  updated {ids[1]} name → {self.store.get(ids[1]).name}")

        # Remove first
        removed = self.store.remove(ids[0])
        self._log(f"  removed {removed.name}")
        self._log(f"  count = {self.store.count()}")

        # Get remaining
        for eid in ids[1:]:
            e = self.store.get(eid)
            self._log(f"  remaining: {eid} → {e.name}")

        # Clear
        self.store.clear()
        self._log(f"  cleared → count = {self.store.count()}")

        self._added_ids.clear()
        self._refresh_status()
        self._log("── Auto-sequence done ──")


def main():
    app = QApplication(sys.argv)
    test_window = StoreTest()
    test_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
