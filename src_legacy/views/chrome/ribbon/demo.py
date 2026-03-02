"""Ribbon demo - shows a simple ribbon with tabs and groups."""
from pathlib import Path
import sys

# Add src folder to path for imports
sys.path.insert(0, str(Path(__file__).parents[3]))

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTextEdit
from PySide6.QtGui import QIcon

from views.chrome.ribbon.widget import Ribbon, RibbonTab, RibbonGroup, RibbonButton
from views.theme import create_demo_app


class DemoWindow(QMainWindow):
    """Demo window showing ribbon usage."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ribbon Demo")
        self.resize(900, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create ribbon
        ribbon = Ribbon()
        
        # Home tab
        home_tab = RibbonTab()
        
        # File group
        file_group = RibbonGroup("File")
        new_btn = RibbonButton("New")
        new_btn.clicked.connect(lambda: self._log("New clicked"))
        open_btn = RibbonButton("Open")
        open_btn.clicked.connect(lambda: self._log("Open clicked"))
        save_btn = RibbonButton("Save")
        save_btn.clicked.connect(lambda: self._log("Save clicked"))
        file_group.add_button(new_btn)
        file_group.add_button(open_btn)
        file_group.add_button(save_btn)
        home_tab.add_group(file_group)
        
        # Edit group
        edit_group = RibbonGroup("Edit")
        cut_btn = RibbonButton("Cut")
        cut_btn.clicked.connect(lambda: self._log("Cut clicked"))
        copy_btn = RibbonButton("Copy")
        copy_btn.clicked.connect(lambda: self._log("Copy clicked"))
        paste_btn = RibbonButton("Paste")
        paste_btn.clicked.connect(lambda: self._log("Paste clicked"))
        edit_group.add_button(cut_btn)
        edit_group.add_button(copy_btn)
        edit_group.add_button(paste_btn)
        home_tab.add_group(edit_group)
        
        ribbon.add_tab(home_tab, "Home")
        
        # View tab
        view_tab = RibbonTab()
        
        # Zoom group
        zoom_group = RibbonGroup("Zoom")
        zoom_in_btn = RibbonButton("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self._log("Zoom In clicked"))
        zoom_out_btn = RibbonButton("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self._log("Zoom Out clicked"))
        fit_btn = RibbonButton("Fit")
        fit_btn.clicked.connect(lambda: self._log("Fit clicked"))
        zoom_group.add_button(zoom_in_btn)
        zoom_group.add_button(zoom_out_btn)
        zoom_group.add_button(fit_btn)
        view_tab.add_group(zoom_group)
        
        ribbon.add_tab(view_tab, "View")
        
        # Analysis tab
        analysis_tab = RibbonTab()
        
        # Core group
        core_group = RibbonGroup("Core")
        calibrate_btn = RibbonButton("Calibrate")
        calibrate_btn.clicked.connect(lambda: self._log("Calibrate clicked"))
        analyze_btn = RibbonButton("Analyze")
        analyze_btn.clicked.connect(lambda: self._log("Analyze clicked"))
        core_group.add_button(calibrate_btn)
        core_group.add_button(analyze_btn)
        analysis_tab.add_group(core_group)
        
        ribbon.add_tab(analysis_tab, "Analysis")
        
        layout.addWidget(ribbon)
        
        # Log area
        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setPlaceholderText("Click ribbon buttons to see actions logged here...")
        layout.addWidget(self._log_area, stretch=1)
    
    def _log(self, message: str) -> None:
        """Log a message to the text area."""
        self._log_area.append(message)


def main() -> None:
    app, _theme = create_demo_app(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
