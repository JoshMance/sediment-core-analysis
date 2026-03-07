"""
Manual test for FileBrowser - Visual verification with signal logging

This manual test shows the FileBrowser widget and logs all signals it emits.
Use this to verify the view component works correctly and emits signals as expected.

Run with: python -m tests.file_browser_test
"""

import sys

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from src.ui.views.shell.file_browser import FileBrowser
from tests.helpers import LogWindow, SignalLogger


class FileBrowserTest(QWidget):
    """Manual test container for FileBrowser with signal logging"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileBrowser Manual Test - View Only")
        self.setGeometry(200, 200, 600, 500)
        
        # Create log window
        self.log_window = LogWindow("FileBrowser Signal Logs")
        
        # Setup layout
        layout = QVBoxLayout()
        
        # Create FileBrowser instance
        self.file_browser = FileBrowser()
        layout.addWidget(self.file_browser)
        
        # Create signal logger
        self.signal_logger = SignalLogger(self.log_window, "FileBrowser")
        
        # Connect all signals to logger
        self.signal_logger.connect_signal(self.file_browser.fileClicked, "fileClicked")
        self.signal_logger.connect_signal(self.file_browser.fileDoubleClicked, "fileDoubleClicked")
        self.signal_logger.connect_signal(self.file_browser.pathChanged, "pathChanged")
        
        self.setLayout(layout)
        
        # Show log window
        self.log_window.show()
        self.log_window.add_log("FileBrowser Test initialized")
        self.log_window.add_log(f"Starting in: {self.file_browser.get_current_path()}")
    
    def closeEvent(self, event):
        """Close log window when main window closes"""
        self.log_window.close()
        super().closeEvent(event)


def main():
    """Run the FileBrowser manual test"""
    app = QApplication(sys.argv)
    
    # Create and show test window
    test = FileBrowserTest()
    test.show()
    
    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()