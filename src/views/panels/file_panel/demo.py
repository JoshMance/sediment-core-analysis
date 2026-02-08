"""Demo script for the FilePanel widget."""
import sys
import os

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QApplication
from views.panels.file_panel.widget import FilePanel


def main():
    app = QApplication(sys.argv)
    
    panel = FilePanel()
    panel.setWindowTitle("File Panel Demo")
    panel.resize(400, 600)
    
    # Connect signals for demonstration
    panel.signals.fileSelected.connect(lambda path: print(f"File selected: {path}"))
    panel.signals.directoryChanged.connect(lambda path: print(f"Directory changed: {path}"))
    
    panel.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
