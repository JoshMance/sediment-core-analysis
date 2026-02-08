# Sediment Core Analysis Toolkit

Open-source desktop application for analysing sediment core images with emphasis on colour metrics, depth-based profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6** (Qt6).

---

## Features

- **Stratigraphy Panel** — Interactive visualization with configurable columns (image, data plots, ruler, layer annotations)
- **Image Panel** — Pan/zoom canvas for core photography with calibration tools
- **File & Workspace Panels** — Project organization and file management
- **Ribbon Toolbar** — Tabbed toolbar with grouped actions (Home, View, Tools, Analysis, Science)
- **Light/Dark Theme** — Full theme support with custom colour palettes

---

## Quick Start

```bash
# Install uv (recommended Python package manager)
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/your-username/sediment-core-analysis.git
cd sediment-core-analysis
uv sync

# Run the main application
uv run main.py --light    # Light theme
uv run main.py --dark     # Dark theme
```

### Run Individual Components

```bash
# Panel demos (all support --dark / --light flags)
uv run src/views/panels/stratigraphy_panel/demo.py --dark
uv run src/views/panels/image_panel/demo.py --light
uv run src/views/panels/file_panel/demo.py
uv run src/views/panels/workspace_panel/demo.py

# Ribbon toolbar demo
uv run src/views/chrome/ribbon/demo.py --dark
```

---

## Project Structure

```
sediment-core-analysis/
├── main.py                          # Application entry point
├── pyproject.toml                   # Dependencies & project config
│
├── src/
│   ├── models/
│   │   └── datatypes/               # Data classes
│   │       ├── image.py             # Image with numpy array data
│   │       ├── core.py              # Sediment core with calibration
│   │       ├── continuous_data.py   # Depth-indexed continuous values
│   │       └── categorical_data.py  # Depth-indexed categorical values
│   │
│   └── views/
│       ├── panels/                  # Reusable panel widgets
│       │   ├── file_panel/          # File system browser
│       │   ├── workspace_panel/     # Project items tree
│       │   ├── image_panel/         # Pan/zoom image canvas
│       │   └── stratigraphy_panel/  # Stratigraphy visualization
│       │       └── columns/         # Column types (image, data, ruler, layer)
│       │
│       ├── chrome/
│       │   └── ribbon/              # Ribbon toolbar widget
│       │       ├── widget.py        # Ribbon, RibbonTab, RibbonGroup, RibbonButton
│       │       └── config.json      # Button definitions
│       │
│       └── theme/
│           ├── theme_colours.py     # Light/dark QPalette definitions
│           └── theme_manager.py     # create_demo_app() helper
│
├── docs/
│   ├── architecture/                # Developer documentation
│   └── guides/                      # User guides
│
└── sandbox/                         # Experiments and prototypes
```

---

## Tech Stack

| Component       | Technology    |
| --------------- | ------------- |
| GUI Framework   | PySide6 (Qt6) |
| Data Processing | NumPy, SciPy  |
| Visualization   | Matplotlib    |
| Image I/O       | imageio, PIL  |
| Package Manager | uv            |

---

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black src/
uv run ruff check src/ --fix
```

### Component Development Pattern

Each panel/widget follows a consistent structure:

```
panel_name/
├── __init__.py      # Public exports
├── widget.py        # Main widget class
├── signals.py       # Qt signals (optional)
└── demo.py          # Standalone demo with --dark/--light support
```

---

## License

MIT License
