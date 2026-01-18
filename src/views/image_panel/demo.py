import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QPixmap

from .widget import ImagePanel

def main():
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()

    # Create the image interaction widget
    widget = ImagePanel()
    window.setCentralWidget(widget)

    # Load the demo image from src/resources/
    # Adjust path relative to the project root
    resources_path = Path(__file__).resolve().parents[2] / "resources"
    demo_image_path = resources_path / "raccoon_face_color.png"

    if demo_image_path.exists():
        pixmap = QPixmap(str(demo_image_path))
        widget.set_image(pixmap)
    else:
        # fallback: blank placeholder
        from PySide6.QtGui import QImage, QColor
        image = QImage(800, 600, QImage.Format_RGB32)
        image.fill(QColor("lightgray"))
        widget.set_image(QPixmap.fromImage(image))

    # Window settings
    window.resize(900, 600)
    window.setWindowTitle("Image Interaction Demo")
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
