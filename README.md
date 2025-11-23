# Sediment Core Analysis Toolkit

Open-source software for analysing sediment core images with a focus on colour metrics and geochemical interpretation.  
Tools include core extraction, colour-space analysis (RGB, CIELAB, Munsell), measurement utilities, and geological annotation.  
Developed as a continuation of the original Sedivis project.

---

## Features

- Core extraction from scanned or photographed images  
- Colour-space analysis (RGB, CIELAB, Munsell)  
- Munsell calibration workflows  
- Depth and distance measurement tools  
- Geological and lithology annotation  
- Export of colour and annotation data (CSV and related formats)

---

## Status

**Early development.**  
Architecture, APIs, and UI components may change as the project evolves.

---

## Project Goals

- Provide a reproducible, science-focused workflow for sediment core analysis  
- Integrate colour metrics with geochemical interpretation  
- Keep UI and analysis logic clearly separated  
- Support scripting and extensible analysis pipelines  

---

## Installation

### Prerequisites

- [.NET 9.0 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) or later

### Build from Source

```bash
git clone https://github.com/JoshMance/sediment-core-analysis.git
cd sediment-core-analysis
dotnet build SedimentCoreApp.sln
```

### Run the Application

```bash
dotnet run --project SedimentCoreApp.UI
```

---

## Project Structure

```plaintext
SedimentCoreApp.UI/
  ├── App.axaml              # Application entry and styling
  ├── App.axaml.cs
  ├── Program.cs             # Application startup
  ├── Views/                 # XAML views and code-behind
  │   ├── MainWindow.axaml
  │   ├── CoreImageView.axaml
  │   └── SidebarView.axaml
  ├── ViewModels/            # MVVM view models
  │   ├── MainWindowViewModel.cs
  │   ├── CoreImageViewModel.cs
  │   └── SidebarViewModel.cs
  └── Assets/                # Images, styles, and resources
      ├── Images/
      └── Styles/
```

The project follows the MVVM (Model-View-ViewModel) architectural pattern for maintainability and testability.

---

## Usage

Documentation and examples will be added as components become available.

---

## Acknowledgements

Developed as a continuation of the original Sedivis project created collaboratively by the commissioning researcher and the student development team.

---

## License

MIT License
