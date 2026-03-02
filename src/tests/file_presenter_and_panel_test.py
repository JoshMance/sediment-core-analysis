"""
Manual test for FilePanel + FilePresenter integration

Tests the complete FilePanel view with FilePresenter working together.
Shows the actual file panel with presenter logic handling file selections.

Run with: python -m src.tests.file_presenter_and_panel_test
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from src.views.panels.file_panel import FilePanel
from src.presenters.file_presenter import FilePresenter
from src.tests.helpers import LogWindow, SignalLogger


class FilePanelWithPresenterTest(QWidget):
    """Integration test for FilePanel with FilePresenter"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FilePanel + FilePresenter Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create log window for monitoring
        self.log_window = LogWindow("FilePanel + FilePresenter Logs", 400, 300)
        self.log_window.show()
        self.log_window.move(850, 100)  # Position next to main window
        
        # Create signal logger (needs log_window)
        self.signal_logger = SignalLogger(self.log_window, "File Panel")
        
        # Create the FilePanel view
        self.file_panel = FilePanel()
        layout.addWidget(self.file_panel)
        
        # Create the FilePresenter and connect it to the view
        self.file_presenter = FilePresenter(self.file_panel)
        
        # Log the setup
        self.log_window.add_log("Created FilePanel view")
        self.log_window.add_log("Created FilePresenter")
        self.log_window.add_log("Connected presenter to view")
        
        # Set up signal logging
        self.signal_logger.connect_signal(
            self.file_panel.fileDoubleClicked, 
            "fileDoubleClicked"
        )
        self.signal_logger.connect_signal(
            self.file_panel.pathChanged, 
            "pathChanged"
        )
        
        self.log_window.add_log("Signal logging configured")
        self.log_window.add_log("Ready! Select files to see presenter output in console")


def main():
    """Run the FilePanel + FilePresenter integration test"""
    app = QApplication(sys.argv)
    
    # Create the test window
    test_window = FilePanelWithPresenterTest()
    test_window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
