# Sediment Core Analysis Toolkit

Open-source software for analysing sediment core images with an emphasis on colour metrics, depth-based profiles, and geochemical interpretation.  
Tools include core extraction, colour-space analysis (RGB, CIELAB, Munsell), depth and measurement utilities, and geological annotation.  

Originally developed as part of the Sedivis project and now being rebuilt with Python + PyQt6.

---

## Technology Stack

**Python + PyQt6** - Modern cross-platform GUI framework

---

## Features (Planned)

- Core extraction from scanned or photographed imagery  
- Colour-space transformations and colour metric reporting  
- Munsell calibration workflow  
- Depth and distance measurement tools  
- Geological and lithology annotation overlays  
- Export of data for further geochemical and statistical analysis  

---

## Quick Start

```bash
# Install uv (if not already installed)
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Run application
uv run python src/main.py
```

---

## Project Structure

```
sediment-core-analysis/
├─ src/
│  └─ main.py                     → application entry point
├─ docs/
│  ├─ architecture/               → developer documentation
│  └─ guides/                     → end-user guidance
├─ science/                       → scientific write-ups and references
└─ pyproject.toml                 → Python project config & dependencies
```

---

## Branch Structure

- **dev** - Active Python/PyQt6 development (current)
- **dev-dotnet** - Archived .NET/Avalonia implementation

---

## Installation

### Requirements

- .NET 9.0 SDK or later

### Build

git clone <https://github.com/JoshMance/sediment-core-analysis.git>  
cd sediment-core-analysis  
dotnet build SedimentCoreApp.sln  

### Run

dotnet run --project src/SedimentCoreApp.UI

---

## Usage

Documentation, examples, and analysis workflows will be added as the tool matures.  
Developer architecture notes will appear in docs/architecture and scientific methods will be documented under science.

---

## Contributing

Contributions are welcome once the architectural foundations are complete. Until then, the focus is on establishing a stable MVP with a reproducible analysis pipeline.

---

## Acknowledgements

This project builds on the original Sedivis work created collaboratively by the commissioning researcher and the student development team.

---

## License

MIT License
