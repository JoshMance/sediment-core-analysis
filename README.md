# Sediment Core Analysis Toolkit

Open-source software for analysing sediment core images with an emphasis on colour metrics, depth-based profiles, and geochemical interpretation.  
Tools include core extraction, colour-space analysis (RGB, CIELAB, Munsell), depth and measurement utilities, and geological annotation.  

Originally developed as part of the Sedivis project and now redesigned with a more modular architecture.

---

## Features

- Core extraction from scanned or photographed imagery  
- Colour-space transformations and colour metric reporting  
- Munsell calibration workflow  
- Depth and distance measurement tools  
- Geological and lithology annotation overlays  
- Export of data for further geochemical and statistical analysis  

---

## Status

**Early development.**  
User interface, APIs, and workflows are expected to evolve as features are stabilised.

---

## Project Structure

This repository uses a layered design to cleanly separate scientific logic, domain modelling, and desktop UI:

sediment-core-analysis/
├─ src/
│  ├─ SedimentCore.Domain/        → core scientific data models
│  ├─ SedimentCore.Analysis/      → numerical + colour analysis logic
│  └─ SedimentCoreApp.UI/         → Avalonia desktop application
├─ docs/
│  ├─ architecture/               → developer documentation
│  └─ guides/                     → end-user guidance
└─ science/                       → scientific write-ups and references

Layering principle:

- Domain describes the world (POCOs for cores, profiles, units)
- Analysis explains it (FFT, PCA, colour conversions, stats)
- UI presents it (Avalonia views + MVVM)
- Docs and science justify it (software rationale + scientific context)

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

Contributions are welcome once the architectural foundations are complete. Until then, the focus is on establishing a stable API and reproducible analysis pipeline.

---

## Acknowledgements

This project builds on the original Sedivis work created collaboratively by the commissioning researcher and the student development team.

---

## License

MIT License
