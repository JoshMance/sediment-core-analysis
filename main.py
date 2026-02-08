"""Main application entry point."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QDockWidget, QFrame, QStatusBar
)
from PySide6.QtCore import Qt

from views.chrome.ribbon import Ribbon


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sediment Core Analysis")
        self.resize(1200, 800)
        
        # Ribbon as a toolbar at top (not in central widget)
        ribbon_container = QWidget()
        ribbon_layout = QVBoxLayout(ribbon_container)
        ribbon_layout.setContentsMargins(0, 0, 0, 0)
        self._ribbon = Ribbon()
        ribbon_layout.addWidget(self._ribbon)
        
        # Add ribbon as a non-movable dock at top
        ribbon_dock = QDockWidget()
        ribbon_dock.setWidget(ribbon_container)
        ribbon_dock.setTitleBarWidget(QWidget())  # Hide title bar
        ribbon_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, ribbon_dock)
        
        # Central content area
        self._content = QFrame()
        self._content.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCentralWidget(self._content)
        
        # Left sidebar
        self._left_dock = QDockWidget("Explorer", self)
        self._left_sidebar = QFrame()
        self._left_sidebar.setMinimumWidth(200)
        self._left_dock.setWidget(self._left_sidebar)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._left_dock)
        
        # Right sidebar
        self._right_dock = QDockWidget("Properties", self)
        self._right_sidebar = QFrame()
        self._right_sidebar.setMinimumWidth(200)
        self._right_dock.setWidget(self._right_sidebar)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._right_dock)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
