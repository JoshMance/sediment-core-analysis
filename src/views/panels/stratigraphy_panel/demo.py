import sys
import os
from pathlib import Path

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from PIL import Image as PILImage
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt

from views.panels.stratigraphy_panel.widget import StratigraphyPanel
from views.panels.stratigraphy_panel.columns import BaseColumn, ImageColumn, DataColumn, RulerColumn, LayerColumn, LayerStyle
from models.datatypes import Image, Core, ContinuousData, CategoricalData


def extract_rgb_from_image(image: Image) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract average R, G, B values for each row of the image.
    
    Returns arrays of shape (height,) with values normalized to 0-1.
    """
    if image.data is None:
        return np.array([]), np.array([]), np.array([])
    
    # image.data is (height, width, 3) RGB numpy array
    # Average across width dimension
    row_means = image.data.mean(axis=1) / 255.0  # (height, 3) normalized
    
    return row_means[:, 0], row_means[:, 1], row_means[:, 2]


def calculate_mean_color_for_depth_range(
    r_data: ContinuousData, 
    g_data: ContinuousData, 
    b_data: ContinuousData,
    start_depth: float, 
    end_depth: float
) -> QColor:
    """Calculate mean RGB color for a depth range from continuous data.
    
    Args:
        r_data, g_data, b_data: RGB channel continuous data
        start_depth, end_depth: Depth range to calculate color for
        
    Returns:
        QColor with the mean RGB values
    """
    if len(r_data) == 0:
        return QColor(255, 255, 255)  # White fallback
    
    # Find indices within the depth range
    positions = r_data.positions
    mask = (positions >= start_depth) & (positions < end_depth)
    
    if not np.any(mask):
        # No data in range - interpolate at midpoint
        mid = (start_depth + end_depth) / 2
        r = r_data.value_at(mid) or 0.5
        g = g_data.value_at(mid) or 0.5
        b = b_data.value_at(mid) or 0.5
    else:
        r = float(np.mean(r_data.values[mask]))
        g = float(np.mean(g_data.values[mask]))
        b = float(np.mean(b_data.values[mask]))
    
    return QColor(int(r * 255), int(g * 255), int(b * 255))


def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setStyleSheet("QMainWindow { background-color: #F0F0F0; }")
    
    # Create the stratigraphy panel
    panel = StratigraphyPanel()
    window.setCentralWidget(panel)
    
    # =====================================================
    # MODEL LAYER: Create datatypes
    # =====================================================
    
    # Load core image
    resources_path = Path(__file__).resolve().parents[3] / "resources"
    core_image_path = resources_path / "core_tester_2.jpg"
    
    if core_image_path.exists():
        pil_image = PILImage.open(core_image_path).convert("RGB")
        image_data = np.array(pil_image, dtype=np.uint8)
        
        # Auto-rotate if wider than tall (horizontal orientation)
        if image_data.shape[1] > image_data.shape[0]:
            image_data = np.rot90(image_data)
        
        core_image = Image(
            name=core_image_path.stem,
            file_path=core_image_path,
            data=image_data
        )
    else:
        # Fallback: create a gradient test image
        image_data = np.zeros((600, 100, 3), dtype=np.uint8)
        image_data[:, :, 0] = np.linspace(100, 200, 600, dtype=np.uint8)[:, np.newaxis]
        image_data[:, :, 1] = np.linspace(80, 160, 600, dtype=np.uint8)[:, np.newaxis]
        image_data[:, :, 2] = np.linspace(60, 120, 600, dtype=np.uint8)[:, np.newaxis]
        
        core_image = Image(name="test_gradient", data=image_data)
    
    # Create Core datatype
    # Calibration: assume 1 mm per pixel for this demo
    core = Core(
        name="Demo Core",
        image=core_image,
        mm_per_px=1.0,  # 1mm per pixel
        layer_boundaries_px=[]  # Will be set by UI dividers
    )
    
    # Extract RGB data as ContinuousData children of the core
    r_values, g_values, b_values = extract_rgb_from_image(core_image)
    
    # Positions are in mm (using core's calibration)
    positions_mm = np.arange(len(r_values)) * core.mm_per_px
    
    r_data = ContinuousData(name="Red", values=r_values, positions=positions_mm, parent=core)
    g_data = ContinuousData(name="Green", values=g_values, positions=positions_mm, parent=core)
    b_data = ContinuousData(name="Blue", values=b_values, positions=positions_mm, parent=core)
    
    # =====================================================
    # VIEW LAYER: Create columns from datatypes
    # =====================================================
    
    # Convert Image datatype to QPixmap for ImageColumn
    # (This is the view-layer conversion - view knows about QPixmap, model doesn't)
    def image_to_pixmap(img: Image) -> QPixmap | None:
        if img.data is None:
            return None
        from PySide6.QtGui import QImage
        h, w, c = img.data.shape
        qimage = QImage(img.data.tobytes(), w, h, c * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qimage)
    
    core_pixmap = image_to_pixmap(core_image)
    
    # Image column
    image_col = ImageColumn("Image", pixmap=core_pixmap, width=70)
    depth_range_mm = core.depth_range_mm or (0.0, 100.0)
    image_col.set_depth_range(depth_range_mm[0], depth_range_mm[1])
    
    # Index column with auto-numbering
    index_col = LayerColumn("Index", width=40, auto_number=True)
    index_col.add_category("numbered", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
    
    # Thickness column with auto-thickness
    thickness_col = LayerColumn("Thickness", width=50, auto_thickness=True)
    thickness_col.add_category("thickness", LayerStyle(color=QColor(0, 0, 0, 0), text_align="center"))
    
    # Munsell column with dynamic color from RGB data
    def munsell_color_callback(row):
        return calculate_mean_color_for_depth_range(
            r_data, g_data, b_data,
            row.min_depth, row.max_depth
        )
    
    munsell_col = LayerColumn("Munsell", width=50, color_callback=munsell_color_callback, hide_text=True)
    
    # RGB data columns (using ContinuousData)
    columns = [
        RulerColumn("Depth", width=40, unit="mm"),
        thickness_col,
        index_col,
        image_col,
        munsell_col,
        DataColumn("Red", data=list(r_data.values), min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.red)),
        DataColumn("Green", data=list(g_data.values), min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.green)),
        DataColumn("Blue", data=list(b_data.values), min_value=0.0, max_value=1.0, width=70, color=QColor(Qt.blue)),
        BaseColumn("Lithology", width=100),
        BaseColumn("Description", width=100),
    ]
    
    # Set columns in panel
    panel.set_columns(columns)
    
    # Add some test dividers (in mm, matching the depth range)
    panel.add_row_divider(25.0)  # Divider at 25mm
    panel.add_row_divider(60.0)  # Divider at 60mm
    
    # Window settings
    window.resize(800, 600)
    window.setWindowTitle("Stratigraphy Panel Demo")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
