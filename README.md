# Sediment Core Analysis Toolkit

Desktop application for analysing sediment core images with colour metrics, depth profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6** (Qt6).

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
uv run main.py
```

### Run Panel Demos

```bash
uv run src/views/panels/stratigraphy_panel/demo.py
uv run src/views/panels/image_panel/demo.py
uv run src/views/panels/file_panel/demo.py
uv run src/views/panels/workspace_panel/demo.py
uv run src/views/chrome/ribbon/demo.py
```

---

## Project Structure

```
sediment-core-analysis/
├── main.py                    # Application entry point
├── pyproject.toml             # Dependencies & config
│
├── src/
│   ├── science/               # Pure compute (no app dependencies)
│   │   ├── api.py             # Public API
│   │   ├── functions/         # Low-level compute
│   │   └── pipelines/         # Higher-level workflows
│   │
│   ├── models/
│   │   ├── datatypes/         # Value types (Image, Layer, Data, etc.)
│   │   ├── entities/          # Domain objects (Core, CoreAnalysis)
│   │   └── services/          # Operations (CoreCreationService, etc.)
│   │
│   └── views/
│       ├── panels/            # Panel widgets
│       │   ├── stratigraphy_panel/
│       │   ├── image_panel/
│       │   ├── file_panel/
│       │   └── workspace_panel/
│       ├── chrome/ribbon/     # Ribbon toolbar
│       └── theme/             # Light/dark theme support
│
└── docs/architecture/         # Architecture documentation
```

See [docs/architecture/PRINCIPLES.md](docs/architecture/PRINCIPLES.md) for architecture details.

---

## Tech Stack

| Component       | Technology    |
| --------------- | ------------- |
| GUI Framework   | PySide6 (Qt6) |
| Data Processing | NumPy, SciPy  |
| Visualization   | Matplotlib    |
| Package Manager | uv            |

---

## Development

```bash
uv sync --all-extras
uv run pytest
uv run black src/
uv run ruff check src/ --fix
```

---

## License

MIT License
