"""Demo script for StratigraphyPanel using the new architecture.

This demo acts as a QUASI-CONTROLLER:
- Creates models (Core, CoreAnalysis) using services
- Wires view callbacks to service operations
- Calls view.refresh() after entity changes

The view RENDERS the entity but does NOT own layer state.
The view CREATES column instances from the model (data-driven).
"""
import sys
import os
from pathlib import Path

# Add src directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from PySide6.QtWidgets import QMainWindow

from views.panels.stratigraphy_panel.widget import StratigraphyPanel
from views.theme import create_demo_app

# Models - using new architecture
from models import (
    Image, ImageCalibration,
    CoreCreationService, CoreAnalysisService,
)


def main():
    app, _theme = create_demo_app(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setStyleSheet("QMainWindow { background-color: #F0F0F0; }")
    
    # Create the stratigraphy panel
    panel = StratigraphyPanel()
    window.setCentralWidget(panel)
    
    # =====================================================
    # MODEL LAYER: Create Core using services
    # =====================================================
    
    resources_path = Path(__file__).resolve().parents[3] / "resources"
    core_image_path = resources_path / "core_tester_2.jpg"
    
    if core_image_path.exists():
        # Use CoreCreationService to load and initialize core
        core = CoreCreationService.create_from_file(
            file_path=core_image_path,
            mm_per_px=1.0,  # 1mm per pixel
        )
    else:
        # Fallback: create a gradient test image
        image_data = np.zeros((600, 100, 3), dtype=np.uint8)
        image_data[:, :, 0] = np.linspace(100, 200, 600, dtype=np.uint8)[:, np.newaxis]
        image_data[:, :, 1] = np.linspace(80, 160, 600, dtype=np.uint8)[:, np.newaxis]
        image_data[:, :, 2] = np.linspace(60, 120, 600, dtype=np.uint8)[:, np.newaxis]
        
        image = Image(name="test_gradient", data=image_data)
        core = CoreCreationService.create_from_image(
            image=image,
            calibration=ImageCalibration(mm_per_px=1.0),
        )
    
    # Create analysis for layer operations
    analysis = CoreAnalysisService.create_analysis(core)
    
    # Initialize with some boundaries using service (in mm depths)
    depth_range_mm = core.depth_range_mm or (0.0, 100.0)
    CoreAnalysisService.create_initial_layers(analysis, [depth_range_mm[0], 25.0, 60.0, depth_range_mm[1]])
    
    # =====================================================
    # CONTROLLER: Wire callbacks to services
    # =====================================================
    
    def on_boundary_add(depth_mm: float) -> None:
        """Handle add boundary request from view."""
        CoreAnalysisService.add_boundary_at_depth(analysis, depth_mm)
        panel.refresh()
    
    def on_boundary_delete(divider_idx: int) -> None:
        """Handle delete boundary request from view."""
        CoreAnalysisService.remove_boundary_at_index(analysis, divider_idx)
        panel.refresh()
    
    def on_boundary_move(divider_idx: int, new_depth_mm: float) -> None:
        """Handle move boundary request from view."""
        CoreAnalysisService.move_boundary(analysis, divider_idx, new_depth_mm)
        panel.refresh()
    
    panel.on_boundary_add = on_boundary_add
    panel.on_boundary_delete = on_boundary_delete
    panel.on_boundary_move = on_boundary_move
    
    # Set the analysis on the panel (view renders from entity)
    panel.set_analysis(analysis)
    
    # Window settings
    window.resize(800, 600)
    window.setWindowTitle("Stratigraphy Panel Demo")
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
