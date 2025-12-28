"""
Sediment Core Analysis Application
Desktop tool for analyzing sediment core imagery
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QTabWidget, QPushButton
)
from PyQt6.QtCore import Qt

from styles import RIBBON_STYLE, RIBBON_TAB_STYLE, WORKSPACE_STYLE, PLACEHOLDER_STYLE


class RibbonTab(QWidget):
    """A single tab in the ribbon interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(RIBBON_TAB_STYLE)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 8, 10, 5)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    """Main application window with ribbon interface"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sediment Core Workbench")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main container
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_container.setLayout(main_layout)
        
        # Ribbon menu
        main_layout.addWidget(self.create_ribbon())
        
        # Main workspace with 3-column layout
        workspace = QWidget()
        workspace.setStyleSheet("background: #f0f0f0;")
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(10, 10, 10, 10)
        workspace_layout.setSpacing(10)
        workspace.setLayout(workspace_layout)
        
        # Left sidebar
        self.left_sidebar = QWidget()
        self.left_sidebar.setStyleSheet("background: white; border: 1px solid #ddd;")
        self.left_sidebar.setFixedWidth(200)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_sidebar.setLayout(left_layout)
        workspace_layout.addWidget(self.left_sidebar)
        
        # Center content area
        self.center_content = QWidget()
        self.center_content.setStyleSheet("background: white; border: 1px solid #ddd;")
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(10, 10, 10, 10)
        self.center_content.setLayout(center_layout)
        
        placeholder = QLabel("Load an image to begin analysis")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(PLACEHOLDER_STYLE)
        center_layout.addWidget(placeholder)
        
        workspace_layout.addWidget(self.center_content)
        
        # Right sidebar
        self.right_sidebar = QWidget()
        self.right_sidebar.setStyleSheet("background: white; border: 1px solid #ddd;")
        self.right_sidebar.setFixedWidth(250)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_sidebar.setLayout(right_layout)
        workspace_layout.addWidget(self.right_sidebar)
        
        main_layout.addWidget(workspace)
    
    def create_ribbon(self):
        """Create MS Word-like tabbed ribbon menu"""
        ribbon = QTabWidget()
        ribbon.setDocumentMode(False)
        ribbon.setMaximumHeight(120)
        ribbon.setStyleSheet(RIBBON_STYLE)
        
        # Set maroon background for the tab bar area
        palette = ribbon.palette()
        from PyQt6.QtGui import QColor
        palette.setColor(ribbon.backgroundRole(), QColor("#7C444E"))
        ribbon.setAutoFillBackground(True)
        ribbon.setPalette(palette)
        
        # Home tab
        home_tab = RibbonTab()
        home_tab.layout.addWidget(self.create_button("Open"))
        home_tab.layout.addWidget(self.create_button("Save"))
        home_tab.layout.addWidget(self.create_button("Export"))
        home_tab.layout.addStretch()
        ribbon.addTab(home_tab, "Home")
        
        # Image tab
        image_tab = RibbonTab()
        image_tab.layout.addWidget(self.create_button("Load Image"))
        image_tab.layout.addWidget(self.create_button("Extract Core"))
        image_tab.layout.addWidget(self.create_button("Crop"))
        image_tab.layout.addStretch()
        ribbon.addTab(image_tab, "Image")
        
        # Analysis tab
        analysis_tab = RibbonTab()
        analysis_tab.layout.addWidget(self.create_button("Color Analysis"))
        analysis_tab.layout.addWidget(self.create_button("Depth Profile"))
        analysis_tab.layout.addWidget(self.create_button("Measurements"))
        analysis_tab.layout.addStretch()
        ribbon.addTab(analysis_tab, "Analysis")
        
        # View tab
        view_tab = RibbonTab()
        view_tab.layout.addWidget(self.create_button("Zoom In"))
        view_tab.layout.addWidget(self.create_button("Zoom Out"))
        view_tab.layout.addWidget(self.create_button("Fit to Window"))
        view_tab.layout.addStretch()
        ribbon.addTab(view_tab, "View")
        
        return ribbon
    
    def create_button(self, text):
        """Create a ribbon button"""
        button = QPushButton(text)
        button.setMinimumHeight(40)
        return button


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
