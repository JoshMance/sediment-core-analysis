import sys
import os
from pathlib import Path

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from PIL import Image as PILImage
from PySide6.QtWidgets import QApplication, QMainWindow

from views.panels.image_panel.widget import ImagePanel
from models.datatypes import Image


def main():
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()

    # Create the image panel widget
    widget = ImagePanel()
    window.setCentralWidget(widget)

    # Load the demo image from src/resources/
    resources_path = Path(__file__).resolve().parents[3] / "resources"
    demo_image_path = resources_path / "raccoon_face_color.png"

    if demo_image_path.exists():
        # Load image with PIL, convert to numpy array
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
        image_data[:, :, 0] = np.linspace(0, 255, 800, dtype=np.uint8)  # Red gradient
        image_data[:, :, 1] = 128  # Green constant
        image_data[:, :, 2] = np.linspace(255, 0, 800, dtype=np.uint8)  # Blue gradient
        
        image = Image(
            name="test_gradient",
            data=image_data
        )

    widget.set_image(image)

    # Window settings
    window.resize(900, 600)
    window.setWindowTitle("Image Panel Demo")
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
