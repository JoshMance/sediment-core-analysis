"""Views package - panels, shell, and theme."""

from .panels import ImagePanel, FilePanel, WorkspacePanel, StratigraphyPanel
from .shell.ribbon import Ribbon
from .theme import ThemeColours, create_demo_app

__all__ = [
    # Panels
    'ImagePanel',
    'FilePanel', 
    'WorkspacePanel',
    'StratigraphyPanel',
    # Shell
    'Ribbon',
    # Theme
    'ThemeColours',
    'create_demo_app',
]