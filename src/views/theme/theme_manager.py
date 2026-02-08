"""Theme manager for running demos with theme support."""
import argparse
from PySide6.QtWidgets import QApplication

from views.theme.theme_colours import ThemeColours


def create_demo_app(argv: list[str]) -> tuple[QApplication, ThemeColours]:
    """Create a QApplication with theme support from command line args.
    
    Args:
        argv: Command line arguments (typically sys.argv)
        
    Returns:
        Tuple of (QApplication, ThemeColours)
        
    Usage:
        --dark  : Force dark mode
        --light : Force light mode
        (neither or both): Use system theme
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dark", action="store_true", help="Force dark mode")
    parser.add_argument("--light", action="store_true", help="Force light mode")
    args, remaining = parser.parse_known_args(argv[1:])
    
    # Create app with remaining args
    app = QApplication([argv[0]] + remaining)
    
    # Use Fusion style for consistent palette support
    app.setStyle("Fusion")
    
    theme_colours = ThemeColours(app)
    
    # Apply theme based on args
    if args.dark and not args.light:
        theme_colours.apply_dark_mode()
    elif args.light and not args.dark:
        theme_colours.apply_light_mode()
    else:
        theme_colours.apply_system_theme()
    
    return app, theme_colours
