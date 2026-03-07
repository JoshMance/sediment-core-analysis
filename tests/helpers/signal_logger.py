"""
SignalLogger helper for capturing and logging Qt signals

Provides a cleaner way to intercept Qt signals for testing without
custom slot methods in every test class.
"""
from PySide6.QtCore import QObject

from .log_window import LogWindow


class SignalLogger(QObject):
    """Helper to log Qt signals to a LogWindow"""
    
    def __init__(self, log_window: LogWindow, source: str = "Signal"):
        super().__init__()
        self.log_window = log_window
        self.source = source
        
    def log_signal(self, signal_name: str, *args):
        """Log a signal with its arguments"""
        if args:
            args_str = ", ".join(str(arg) for arg in args)
            message = f"{signal_name}({args_str})"
        else:
            message = f"{signal_name}()"
        self.log_window.add_log(message, self.source)
        
    def connect_signal(self, signal, signal_name: str):
        """Connect a signal to be logged"""
        signal.connect(lambda *args: self.log_signal(signal_name, *args))
