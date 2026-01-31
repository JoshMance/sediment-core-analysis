import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtCore import Qt

from .widget import StratigraphyPanel
from .columns import BaseColumn, ImageColumn, DataColumn, RulerColumn, LayerColumn, LayerStyle


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


def calculate_mean_color_for_depth_range(r_data: list[float], g_data: list[float], b_data: list[float], 
                                          start_depth: float, end_depth: float, 
                                          depth_range: tuple[float, float]) -> QColor:
    """Calculate the mean RGB color for a depth range from the image data.
    
    Args:
        r_data, g_data, b_data: RGB channel data (0-1) for each pixel row in image
        start_depth, end_depth: The depth range to calculate color for
        depth_range: The full (min, max) depth range that the image represents
        
    Returns:
        QColor with the mean RGB values
    """
    if not r_data or not g_data or not b_data:
        return QColor(255, 255, 255)  # White fallback
    
    min_depth, max_depth = depth_range
    depth_span = max_depth - min_depth
    
    if depth_span == 0:
        return QColor(255, 255, 255)
    
    # Convert depth to pixel indices
    start_idx = int((start_depth - min_depth) / depth_span * len(r_data))
    end_idx = int((end_depth - min_depth) / depth_span * len(r_data))
    
    # Clamp to valid range
    start_idx = max(0, min(start_idx, len(r_data) - 1))
    end_idx = max(0, min(end_idx, len(r_data)))
    
    if start_idx >= end_idx:
        end_idx = start_idx + 1
    
    # Calculate mean RGB values for this depth range
    r_mean = sum(r_data[start_idx:end_idx]) / (end_idx - start_idx)
    g_mean = sum(g_data[start_idx:end_idx]) / (end_idx - start_idx)
    b_mean = sum(b_data[start_idx:end_idx]) / (end_idx - start_idx)
    
    # Convert from 0-1 to 0-255
    return QColor(int(r_mean * 255), int(g_mean * 255), int(b_mean * 255))


def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setStyleSheet("QMainWindow { background-color: #F0F0F0; }")
    
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
    image_col = ImageColumn("Image", pixmap=core_pixmap, width=70)
    image_col.set_depth_range(0.0, 100.0)  # Image represents 0-100cm depth
    
    # Extract RGB data from the ROTATED pixmap that's actually displayed
    if image_col.get_pixmap():
        r_data, g_data, b_data = extract_rgb_from_image(image_col.get_pixmap())
    
    # Create index column with auto-numbering enabled
    index_col = LayerColumn("Index", width=40, auto_number=True)
    # Add transparent background style for numbered rows (no background fill)
    index_col.add_category("numbered", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
    
    # Create thickness column with auto-thickness enabled
    thickness_col = LayerColumn("Thickness", width=50, auto_thickness=True)
    thickness_col.add_category("thickness", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
    
    # Create Munsell column with dynamic color calculation (no text, just background color)
    def munsell_color_callback(row):
        return calculate_mean_color_for_depth_range(
            r_data, g_data, b_data,
            row.min_depth, row.max_depth,
            (0.0, 100.0)
        )
    
    munsell_col = LayerColumn("Munsell", width=50, color_callback=munsell_color_callback, hide_text=True)
    
    # Create 9 columns: Ruler (Depth), Thickness, Index, Image, 3 RGB data columns, 2 right
    columns = [
        RulerColumn("Depth", width=40, unit="mm"),
        thickness_col,
        index_col,
        image_col,
        munsell_col,
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
    window.setWindowTitle("Stratigraphy Panel Demo")
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
