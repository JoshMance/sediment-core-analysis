"""CoreStudioPresenter — connects the Core Studio panel to Store and AppController."""
from __future__ import annotations

from PySide6.QtCore import QObject

from src.application import AppController
from src.domain.store import Store
from src.ui.views.panels.core_studio_panel import CoreStudioPanel


class CoreStudioPresenter(QObject):
    """Wires a CoreStudioPanel to the Store and AppController.

    Currently a minimal shell. Future work will handle image drop,
    vertical display, and CoreEntity creation.
    """

    def __init__(
        self,
        view: CoreStudioPanel,
        store: Store,
        controller: AppController,
    ) -> None:
        super().__init__()
        self._view = view
        self._store = store
        self._controller = controller
