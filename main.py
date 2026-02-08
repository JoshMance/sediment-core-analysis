"""Main application entry point."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QDockWidget, QFrame, 
    QStatusBar, QTabWidget, QLabel
)
from PySide6.QtCore import Qt

from views.chrome.ribbon import Ribbon
from views.theme import create_demo_app


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sediment Core Analysis")
        self.resize(1200, 800)
        
        self._setup_ribbon()
        self._setup_central_workspace()
        self._setup_left_dock()
        self._setup_right_dock()
        self._setup_status_bar()
    
    def _setup_ribbon(self) -> None:
        """Create ribbon toolbar at top."""
        ribbon_container = QWidget()
        ribbon_layout = QVBoxLayout(ribbon_container)
        ribbon_layout.setContentsMargins(0, 0, 0, 0)
        self._ribbon = Ribbon()
        ribbon_layout.addWidget(self._ribbon)
        
        ribbon_dock = QDockWidget()
        ribbon_dock.setWidget(ribbon_container)
        ribbon_dock.setTitleBarWidget(QWidget())  # Hide title bar
        ribbon_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, ribbon_dock)
    
    def _setup_central_workspace(self) -> None:
        """Create central tabbed workspace for main content."""
        self._workspace = QTabWidget()
        self._workspace.setTabsClosable(True)
        self._workspace.setMovable(True)
        self._workspace.setDocumentMode(True)
        
        # Placeholder tabs (will be replaced with actual panels)
        image_placeholder = self._create_placeholder("Image Panel")
        strat_placeholder = self._create_placeholder("Stratigraphy Panel")
        
        self._workspace.addTab(image_placeholder, "Core Image")
        self._workspace.addTab(strat_placeholder, "Stratigraphy")
        
        self.setCentralWidget(self._workspace)
    
    def _setup_left_dock(self) -> None:
        """Create left dock for explorer/file browser."""
        self._left_dock = QDockWidget("Explorer", self)
        self._left_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        
        # Placeholder (will be file_panel or workspace_panel)
        explorer = self._create_placeholder("File Explorer")
        explorer.setMinimumWidth(200)
        self._left_dock.setWidget(explorer)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._left_dock)
    
    def _setup_right_dock(self) -> None:
        """Create right dock for properties/settings."""
        self._right_dock = QDockWidget("Properties", self)
        self._right_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        
        # Placeholder (will be properties panel)
        properties = self._create_placeholder("Properties")
        properties.setMinimumWidth(200)
        self._right_dock.setWidget(properties)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._right_dock)
    
    def _setup_status_bar(self) -> None:
        """Create status bar at bottom."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")
    
    def _create_placeholder(self, name: str) -> QFrame:
        """Create a placeholder frame with a label."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return frame


def main() -> None:
    app, _theme = create_demo_app(sys.argv)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
