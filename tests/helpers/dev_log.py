"""Dev-mode signal monitor -- watches QObjects and logs every signal."""

from PySide6.QtCore import QObject

from .log_window import LogWindow
from .signal_logger import SignalLogger


class DevLog:
    """Call watch() on any QObject to auto-log all its signals."""

    def __init__(self) -> None:
        self._window = LogWindow("Dev Log", width=600, height=500)
        self._loggers: list[SignalLogger] = []

    def watch(self, name: str, obj: QObject) -> None:
        """Auto-connect every signal on obj to the log window."""
        logger = SignalLogger(self._window, name)
        logger.connect_all(obj)
        self._loggers.append(logger)

    def show(self) -> None:
        self._window.show()
