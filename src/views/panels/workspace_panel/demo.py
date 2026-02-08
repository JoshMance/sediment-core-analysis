"""Demo script for the WorkspacePanel widget."""
import sys
import os

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from pathlib import Path
from views.panels.workspace_panel.widget import WorkspacePanel
from views.theme import create_demo_app
from models.datatypes import Image


def main():
    app, _theme = create_demo_app(sys.argv)
    
    # Create panel with default columns and formatter
    panel = WorkspacePanel()
    panel.setWindowTitle("Workspace Panel Demo")
    panel.resize(500, 400)
    
    # Add some demo items
    # Create a dummy image (100x100 RGB)
    dummy_image_data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    item1 = Image(
        name="Sample Image 1",
        file_path=Path("sample1.png"),
        data=dummy_image_data
    )
    
    item2 = Image(
        name="Core Photo",
        file_path=Path("core_photo.jpg"),
        data=np.zeros((200, 150, 3), dtype=np.uint8)
    )
    
    item3 = Image(
        name="Untitled",
        data=None
    )
    
    panel.add_item(item1)
    panel.add_item(item2)
    panel.add_item(item3)
    
    # Connect signals for demonstration
    panel.signals.itemSelected.connect(lambda item: print(f"Selected: {item.name}"))
    panel.signals.itemDoubleClicked.connect(lambda item: print(f"Double-clicked: {item.name}"))
    panel.signals.itemRemoved.connect(lambda item: print(f"Removed: {item.name}"))
    
    panel.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
