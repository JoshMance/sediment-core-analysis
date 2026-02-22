"""Demo for ImagePanel showing callback-based architecture.

The demo acts as a quasi-controller:
- Wires callbacks from the panel
- Handles domain logic (Core creation) via services
- The panel itself only displays and emits UI events
"""

import sys
import os
from pathlib import Path

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from PIL import Image as PILImage
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QMainWindow

from views.panels.image_panel.widget import ImagePanel
from views.theme import create_demo_app
from models import Image, ImageCalibration, CoreCreationService


def pixmap_to_ndarray(pixmap: QPixmap) -> np.ndarray:
    """Convert QPixmap to numpy array (RGB)."""
    qimage = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
    w, h = qimage.width(), qimage.height()
    bytes_per_line = qimage.bytesPerLine()
    ptr = qimage.bits()
    
    # Account for scanline padding by using bytesPerLine
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, bytes_per_line))
    # Extract only the actual image data (3 bytes per pixel)
    return arr[:, :w*3].reshape((h, w, 3)).copy()


def main():
    app, _theme = create_demo_app(sys.argv)

    # Create main window
    window = QMainWindow()

    # Create the image panel widget
    panel = ImagePanel()
    window.setCentralWidget(panel)

    # --- Callback handlers (domain logic lives here, not in the panel) ---
    
    def handle_selection_confirmed(pixmap: QPixmap, mm_per_px: float | None) -> None:
        """Handle confirmed selection: create Core entity via service."""
        # Convert pixmap to Image datatype
        image_data = pixmap_to_ndarray(pixmap)
        image = Image(name="Cropped Core", data=image_data)
        
        # Create calibration (default 0.5 mm/px if not provided)
        calibration = ImageCalibration(mm_per_px=mm_per_px or 0.5)
        
        # Create Core using service
        core = CoreCreationService.create_from_image(image, calibration)
        
        print(f"Created Core: {core.name}")
        print(f"  - Height: {core.height_mm:.1f} mm")
        print(f"  - Width: {core.width_mm:.1f} mm")
        print(f"  - Calibration: {calibration.mm_per_px} mm/px")
    
    def handle_calibration_confirmed(mm_per_px: float) -> None:
        """Handle calibration value confirmed."""
        print(f"Calibration confirmed: {mm_per_px} mm/px")
    
    # Wire callbacks
    panel.on_selection_confirmed = handle_selection_confirmed
    panel.on_calibration_confirmed = handle_calibration_confirmed

    # --- Load demo image ---
    
    resources_path = Path(__file__).resolve().parents[3] / "resources"
    demo_image_path = resources_path / "raccoon_face_color.png"

    if demo_image_path.exists():
        pil_image = PILImage.open(demo_image_path).convert("RGB")
        image_data = np.array(pil_image, dtype=np.uint8)
        
        image = Image(
            name=demo_image_path.stem,
            file_path=demo_image_path,
            data=image_data
        )
    else:
        # Fallback: create a gradient test image
        image_data = np.zeros((600, 800, 3), dtype=np.uint8)
        image_data[:, :, 0] = np.linspace(0, 255, 800, dtype=np.uint8)
        image_data[:, :, 1] = 128
        image_data[:, :, 2] = np.linspace(255, 0, 800, dtype=np.uint8)
        
        image = Image(name="test_gradient", data=image_data)

    panel.set_image(image)

    # Window settings
    window.resize(900, 600)
    window.setWindowTitle("Image Panel Demo")
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
