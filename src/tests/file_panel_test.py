"""
Manual test for FilePanel - Visual verification with signal logging

This manual test shows the FilePanel widget and logs all signals it emits.
Use this to verify the view component works correctly and emits signals as expected.

Run with: python -m src.tests.file_panel_test
"""

import sys

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from src.views.panels.file_panel import FilePanel
from src.tests.helpers import LogWindow, SignalLogger


class FilePanelTest(QWidget):
    """Manual test container for FilePanel with signal logging"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FilePanel Manual Test - View Only")
        self.setGeometry(200, 200, 600, 500)
        
        # Create log window
        self.log_window = LogWindow("FilePanel Signal Logs")
        
        # Setup layout
        layout = QVBoxLayout()
        
        # Create FilePanel instance
        self.file_panel = FilePanel()
        layout.addWidget(self.file_panel)
        
        # Create signal logger
        self.signal_logger = SignalLogger(self.log_window, "FilePanel")
        
        # Connect all signals to logger
        self.signal_logger.connect_signal(self.file_panel.fileClicked, "fileClicked")
        self.signal_logger.connect_signal(self.file_panel.fileDoubleClicked, "fileDoubleClicked")
        self.signal_logger.connect_signal(self.file_panel.pathChanged, "pathChanged")
        self.signal_logger.connect_signal(self.file_panel.fileSelected, "fileSelected")
        
        self.setLayout(layout)
        
        # Show log window
        self.log_window.show()
        self.log_window.add_log("FilePanel Test initialized")
        self.log_window.add_log(f"Starting in: {self.file_panel.get_current_path()}")
    
    def closeEvent(self, event):
        """Close log window when main window closes"""
        self.log_window.close()
        super().closeEvent(event)


def main():
    """Run the FilePanel manual test"""
    app = QApplication(sys.argv)
    
    # Create and show test window
    test = FilePanelTest()
    test.show()
    
    # Run Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()