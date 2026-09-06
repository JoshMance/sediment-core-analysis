# Sediment Core Analysis Toolkit

Desktop application for analyzing sediment core images with colour metrics, depth profiles, and stratigraphic interpretation.

Built with **Python 3.10+** and **PySide6**.

---

## Quick Start

```bash
# Install uv (Python package manager)
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/your-username/sediment-core-analysis.git
cd sediment-core-analysis
uv sync

# Run
uv run python main.py

# Optional flags
uv run python main.py --dark
uv run python main.py --light
uv run python main.py --dev   # opens signal log window
```

---

## Project Structure

```text
src/
├── domain/        # Entities, Store
├── application/   # AppController, WorkspaceState, services
└── ui/            # Presenters, views

science/           # Cross-cutting scientific transforms + reference data

docs/
├── architecture/  # Overview, topology, diagrams
├── planning/      # Feature notes
└── principles.md  # Architectural principles and DRY checklist

tests/
```

---

## Development

```bash
uv sync --all-extras
uv run black src/
uv run ruff check src/ --fix
uv run pytest
```

See [docs/architecture/overview.md](docs/architecture/overview.md) for architecture, [docs/development/checklist.md](docs/development/checklist.md) for dev-cycle checks, and [docs/development/implementation_checklist.md](docs/development/implementation_checklist.md) for panel/science change checklists.

---

## License

MIT License
