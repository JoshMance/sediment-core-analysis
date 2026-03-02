"""Theme colour palettes for light/dark mode."""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class ThemeColours:
    """Handles light/dark mode colour switching for a PySide6 application."""
    
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._dark_palette = self._create_dark_palette()
        self._light_palette = self._create_light_palette()
        self._is_dark = False
    
    def _create_dark_palette(self) -> QPalette:
        """Create a dark mode palette."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        return palette
    
    def _create_light_palette(self) -> QPalette:
        """Create a light mode palette."""
        palette = QPalette()
        # Main backgrounds - clean white/light grey
        palette.setColor(QPalette.ColorRole.Window, QColor(248, 248, 248))  # #f8f8f8
        palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))  # #333
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))  # white
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 248, 248))  # #f8f8f8
        # Tooltips
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(51, 51, 51))
        # Text
        palette.setColor(QPalette.ColorRole.Text, QColor(51, 51, 51))  # #333
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(153, 153, 153))  # #999
        # Buttons
        palette.setColor(QPalette.ColorRole.Button, QColor(248, 248, 248))  # #f8f8f8
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(51, 51, 51))  # #333
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        # Accent - Windows blue from old styles
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 212))  # #0078d4
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))  # #0078d4
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        # Borders/frames
        palette.setColor(QPalette.ColorRole.Light, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(227, 227, 227))
        palette.setColor(QPalette.ColorRole.Mid, QColor(204, 204, 204))  # #ccc
        palette.setColor(QPalette.ColorRole.Dark, QColor(160, 160, 160))
        palette.setColor(QPalette.ColorRole.Shadow, QColor(105, 105, 105))
        return palette
    
    @property
    def is_dark(self) -> bool:
        """Whether dark mode is currently active."""
        return self._is_dark
    
    def apply_dark_mode(self) -> None:
        """Switch to dark mode."""
        self._app.setPalette(self._dark_palette)
        self._is_dark = True
    
    def apply_light_mode(self) -> None:
        """Switch to light mode."""
        self._app.setPalette(self._light_palette)
        self._is_dark = False
    
    def toggle(self) -> None:
        """Toggle between dark and light mode."""
        if self._is_dark:
            self.apply_light_mode()
        else:
            self.apply_dark_mode()
    
    def apply_system_theme(self) -> None:
        """Detect and apply the system theme."""
        palette = self._app.palette()
        # If window color is dark, system is in dark mode
        if palette.color(QPalette.ColorRole.Window).lightness() < 128:
            self.apply_dark_mode()
        else:
            self.apply_light_mode()
