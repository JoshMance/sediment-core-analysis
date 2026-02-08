"""Ribbon widget - tabbed toolbar for application actions."""
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QToolButton,
    QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon


# Default config path
_CONFIG_PATH = Path(__file__).parent / "config.json"


class RibbonButton(QToolButton):
    """A button styled for use in a ribbon group."""
    
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(32, 32))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(60)


class RibbonGroup(QFrame):
    """A labeled group of ribbon buttons."""
    
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 2)
        layout.setSpacing(2)
        
        # Button container
        self._button_layout = QHBoxLayout()
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self._button_layout.setSpacing(2)
        layout.addLayout(self._button_layout, stretch=1)
        
        # Group title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(title_label)
        
        # Styling
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            RibbonGroup {
                border-right: 1px solid #ddd;
                background: transparent;
            }
        """)
    
    def add_button(self, button: RibbonButton) -> None:
        """Add a button to this group."""
        self._button_layout.addWidget(button)
    
    def add_widget(self, widget: QWidget) -> None:
        """Add any widget to this group."""
        self._button_layout.addWidget(widget)


class RibbonTab(QWidget):
    """A single tab in the ribbon containing groups of actions."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(8)
        self._layout.addStretch()  # Push groups to the left
    
    def add_group(self, group: RibbonGroup) -> None:
        """Add a group to this tab."""
        # Insert before the stretch
        self._layout.insertWidget(self._layout.count() - 1, group)


class Ribbon(QWidget):
    """Main ribbon widget with tabs containing grouped actions."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._tabs)
        
        # Styling
        self.setStyleSheet("""
            Ribbon {
                background-color: #f5f5f5;
                border-bottom: 1px solid #ccc;
            }
            QTabWidget::pane {
                border: none;
                background-color: #f9f9f9;
            }
            QTabBar::tab {
                padding: 6px 16px;
                background-color: transparent;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #f9f9f9;
                border-bottom: 2px solid #0078d4;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8e8e8;
            }
        """)
        
        self.setFixedHeight(120)
        
        # Store buttons by name for signal connections
        self._buttons: dict[str, RibbonButton] = {}
        
        # Load from config
        self._load_config()
    
    def _load_config(self) -> None:
        """Load ribbon structure from config.json."""
        with open(_CONFIG_PATH) as f:
            config = json.load(f)
        
        for tab_config in config.get("tabs", []):
            tab = RibbonTab()
            
            for group_config in tab_config.get("groups", []):
                group = RibbonGroup(group_config["name"])
                
                for button_name in group_config.get("buttons", []):
                    button = RibbonButton(button_name)
                    group.add_button(button)
                    self._buttons[button_name] = button
                
                tab.add_group(group)
            
            self.add_tab(tab, tab_config["name"])
    
    def add_tab(self, tab: RibbonTab, title: str) -> None:
        """Add a tab to the ribbon."""
        self._tabs.addTab(tab, title)
    
    def current_tab_index(self) -> int:
        """Get the current tab index."""
        return self._tabs.currentIndex()
    
    def set_current_tab(self, index: int) -> None:
        """Set the current tab by index."""
        self._tabs.setCurrentIndex(index)
    
    def get_button(self, name: str) -> RibbonButton | None:
        """Get a button by name."""
        return self._buttons.get(name)
