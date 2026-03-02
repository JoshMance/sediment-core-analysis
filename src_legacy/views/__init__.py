"""Views package - panels, chrome, and theme."""

from .panels import ImagePanel, FilePanel, WorkspacePanel, StratigraphyPanel
from .chrome.ribbon import Ribbon
from .theme import ThemeColours, create_demo_app

__all__ = [
    # Panels
    'ImagePanel',
    'FilePanel', 
    'WorkspacePanel',
    'StratigraphyPanel',
    # Chrome
    'Ribbon',
    # Theme
    'ThemeColours',
    'create_demo_app',
]