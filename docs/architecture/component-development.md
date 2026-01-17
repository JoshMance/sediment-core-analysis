# Component Development Guide

## Philosophy

Each PyQt6 component is developed and tested in isolation before integration into the main application. This approach provides:

- **Faster iteration** - Test individual components without running the full app
- **Clearer boundaries** - Each component has well-defined responsibilities
- **Easier debugging** - Isolate issues to specific components
- **Reusability** - Components can be reused across different parts of the app

---

## Structure

```
src/
├─ components/
│  ├─ __init__.py                    → Package initialization
│  ├─ imageViewer.py                 → ImageViewer component
│  ├─ test_imageViewer.py            → Test harness for ImageViewer
│  ├─ depthScale.py                  → DepthScale component (planned)
│  ├─ test_depthScale.py             → Test harness for DepthScale
│  └─ ...                            → Other components
├─ main.py                           → Main application (integration)
└─ styles.py                         → Shared styles
```

---

## Component Pattern

Each component follows this structure:

### Component File (`componentName.py`)

```python
"""
Component Name
Brief description of what it does
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

class ComponentName(QWidget):
    """
    Component description and responsibilities
    """
    
    # Signals for communication
    dataChanged = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize UI elements"""
        pass
    
    # Public API methods
    def do_something(self, data):
        """Public method for component interaction"""
        pass
```

### Test Harness (`test_componentName.py`)

```python
"""
Test harness for ComponentName
Run directly: uv run python src/components/test_componentName.py
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from componentName import ComponentName

class TestWindow(QMainWindow):
    """Test window with controls to exercise the component"""
    
    def __init__(self):
        super().__init__()
        self.component = ComponentName()
        # Add controls and connect signals
        
def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## Testing a Component

Run any component's test harness directly:

```bash
uv run python src/components/test_imageViewer.py
```

This launches a minimal window with:

- The component being tested
- Control buttons to exercise its features
- Status displays to observe behavior

---

## Integration Strategy

Once components are stable:

1. Import components into `main.py`
2. Arrange them in the main window layout
3. Connect signals between components for state management
4. Add application-level orchestration logic

---

## Planned Components

- **ImageViewer** - Display and manipulate core images (in progress)
- **DepthScale** - Vertical ruler with depth measurements
- **ColourProfile** - Chart showing colour metrics vs depth
- **AnnotationLayer** - Overlay for geological markers
- **MeasurementTools** - Distance and area measurement widgets
- **DataExport** - Export data to CSV/Excel formats
- **MunsellCalibration** - Colour calibration workflow

---

## Benefits of This Approach

- Components can be developed in parallel
- Each component can be demonstrated independently
- Easier to onboard contributors to specific components
- Reduces cognitive load during development
- Makes testing more targeted and effective
