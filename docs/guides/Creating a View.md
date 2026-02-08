# Creating a New View (Panel)

This guide explains the architecture and boilerplate required to add a new view (panel) to the application.

---

## 1. Folder Structure

- Create a new folder under `src/views/` (e.g., `my_panel/`).
- Add an `__init__.py` to make it a package.
- Add a `widget.py` file for your main panel class.

## 2. Main Widget Boilerplate

- Subclass `QWidget` for your main panel class in `widget.py`.
- Set up the layout, toolbar, and main content area in the constructor.
- Implement any overlay or helper widgets as needed.
- Example:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar

class MyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.toolbar = QToolBar()
        layout.addWidget(self.toolbar)
        # Add your main content widget(s) here
```

- Expose your panel in `__init__.py`:

```python
from .widget import MyPanel
__all__ = ['MyPanel']
```

## 3. Optional: Supporting Files

- Only add subfolders like `modals/` or `columns/` if your view requires modular UI components or complex structures. These are not required for all views.
- Add a `signals.py` if you need custom Qt signals for event handling.
- Add other files (e.g., `canvas.py`) as needed for custom drawing or interaction.

## 4. Signals, State Management, and Controller Interaction

- **Signals:** Use a `signals.py` file to define custom signals if your view needs to communicate events.
- **State Management:** Implement state variables and update methods within your widget class. Use signals/slots for reactive updates.
- **Controller Interaction:** If your view interacts with controllers or models, import and use them as needed. Keep UI logic separate from 'business' logic.

## 5. Demo and Testing

- Add a `demo.py` in your panel folder to provide a runnable example of your view.
- Example command to run a demo:
  ```sh
  python src/views/my_panel/demo.py
  ```

## 6. General Principles

- Keep UI logic in the view/widget classes.
- Use signals and slots for communication between UI components.
- Only add complexity (subfolders, extra files) as needed for your specific view.
- Follow the structure and patterns of existing panels for consistency.

---

## [Leave space here for detailed explanation on:]

- Recreating signals (custom event handling)
- State management patterns
- Controller interaction and data flow

---

For more details, review the code in `src/views/image_panel/` and `src/views/stratigraphy_panel/`.

For more details, review the code in `src/views/image_panel/` and `src/views/stratigraphy_panel/`.
