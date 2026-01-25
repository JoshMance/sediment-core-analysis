import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtCore import Qt

from .widget import StratigraphyPanel
from .columns import BaseColumn, ImageColumn, DataColumn, RulerColumn


def extract_rgb_from_image(pixmap: QPixmap) -> tuple[list[float], list[float], list[float]]:
    """Extract average R, G, B values for each horizontal slice of the image."""
    if not pixmap or pixmap.isNull():
        return [], [], []
    
    image = pixmap.toImage()
    width = image.width()
    height = image.height()
    
    r_values = []
    g_values = []
    b_values = []
    
    # For each horizontal slice (row)
    for y in range(height):
        r_sum = 0
        g_sum = 0
        b_sum = 0
        
        # Average across the width
        for x in range(width):
            color = image.pixelColor(x, y)
            r_sum += color.red()
            g_sum += color.green()
            b_sum += color.blue()
        
        # Normalize to 0-1 range (RGB is 0-255)
        r_values.append(r_sum / (width * 255.0))
        g_values.append(g_sum / (width * 255.0))
        b_values.append(b_sum / (width * 255.0))
    
    return r_values, g_values, b_values


def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    
    # Create the stratigraphy panel
    panel = StratigraphyPanel()
    window.setCentralWidget(panel)
    
    # Load core image
    resources_path = Path(__file__).resolve().parents[2] / "resources"
    core_image_path = resources_path / "core_tester_2.jpg"
    
    core_pixmap = None
    r_data, g_data, b_data = [], [], []
    
    if core_image_path.exists():
        core_pixmap = QPixmap(str(core_image_path))
    
    # Create image column that defines the scale
    # Let's say this core represents 0-100 cm of depth
    image_col = ImageColumn("Image", pixmap=core_pixmap, width=80)
    image_col.set_depth_range(0.0, 100.0)  # Image represents 0-100cm depth
    
    # Extract RGB data from the ROTATED pixmap that's actually displayed
    if image_col.get_pixmap():
        r_data, g_data, b_data = extract_rgb_from_image(image_col.get_pixmap())
    
    # Create 8 columns: Ruler (Depth), Thickness, Image, 3 RGB data columns, 2 right
    columns = [
        RulerColumn("Depth", width=50, unit="mm"),
        BaseColumn("Thickness", width=50),
        image_col,
        BaseColumn("Munsell", width=100),
        DataColumn("Red", data=r_data, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.red)),
        DataColumn("Green", data=g_data, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.green)),
        DataColumn("Blue", data=b_data, min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.blue)),
        BaseColumn("Lithology", width=100),
        BaseColumn("Description", width=100),
    ]
    
    # Set columns in panel
    panel.set_columns(columns)
    
    # Add some test dividers (can be dragged in the UI)
    panel.add_row_divider(25.0)  # Divider at 25cm
    panel.add_row_divider(60.0)  # Divider at 60cm
    
    # Window settings
    window.resize(800, 600)
    window.setWindowTitle("Stratigraphy Panel Demo - Drag dividers to move them")
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
