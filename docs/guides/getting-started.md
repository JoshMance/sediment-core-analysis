# Getting Started with Sediment Core Analysis

## Introduction

This guide is for developers, contributors, and students who want to set up a local development environment for the **Sediment Core Analysis** project.

The main desktop application is a PyQt6-based GUI located at `src/main.py`. The project uses Python for scientific computation, image processing, and UI.

---

## Prerequisites

Before you begin, ensure you have the following tools installed:

### Required Tools

- **Python 3.10+**
  - Download from [python.org](https://www.python.org/downloads/)
  - Verify installation: `python --version`
  
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - Linux/Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Verify: `uv --version`

- **Git** for cloning the repository
  - Download from [git-scm.com](https://git-scm.com/)

### Recommended IDE

- **[Visual Studio Code](https://code.visualstudio.com/)**
  - Install the **Python** extension
  - Install the **Pylance** extension for better type checking

- **[PyCharm](https://www.jetbrains.com/pycharm/)** (Community or Professional)
  - Built-in Python support
  - Free Community edition or Professional free for students

### Supported Platforms

PyQt6 supports:

- ✅ **Windows** 10/11
- ✅ **macOS** 10.15+
- ✅ **Linux** (Ubuntu, Fedora, Debian, etc.)

---

## Cloning the Repository

Open a terminal and run:

```bash
git clone https://github.com/JoshMance/sediment-core-analysis.git
cd sediment-core-analysis
```

You should now be in the root of the repository where the `SedimentCoreApp.sln` solution file is located.

---

## Project Layout Overview

The `src/` folder contains three C# projects:

```text
src/
├─ SedimentCore.Domain/
│  └─ Core scientific data models (CoreMetadata, DepthPoint, ColourProfile, etc.)
│     Pure POCOs with no logic—just data structures.
│
├─ SedimentCore.Analysis/
│  └─ Numerical and colour analysis algorithms (FFT, PCA, RGB↔Lab conversions, depth alignment)
│     Single source of truth for scientific computation.
│     References: SedimentCore.Domain
│
└─ SedimentCoreApp.UI/
   └─ Avalonia desktop application (MVVM architecture, Views, ViewModels)
      References: SedimentCore.Domain, SedimentCore.Analysis
```

The layering principle ensures:

- **Domain** describes the world (data models)
- **Analysis** explains it (algorithms)
- **UI** presents it (desktop interface)

---

## Building the Solution

From the repository root, run:

```bash
dotnet build SedimentCoreApp.sln
```

### Successful Build Output

You should see output similar to:

```text
Restore complete (1.3s)
  SedimentCore.Domain succeeded (0.4s) → src\SedimentCore.Domain\bin\Debug\net9.0\SedimentCore.Domain.dll
  SedimentCore.Analysis succeeded (0.5s) → src\SedimentCore.Analysis\bin\Debug\net9.0\SedimentCore.Analysis.dll
  SedimentCoreApp.UI succeeded (3.7s) → src\SedimentCoreApp.UI\bin\Debug\net9.0\SedimentCoreApp.UI.dll

Build succeeded in 5.9s
```

### Common Build Issues

| Problem | Solution |
|---------|----------|
| `error: The current .NET SDK does not support targeting .NET 9.0` | Install [.NET 9.0 SDK](https://dotnet.microsoft.com/download/dotnet/9.0) or later |
| `error: Project file does not exist` | Ensure you're in the repository root (where `SedimentCoreApp.sln` is located) |
| NuGet package restore failures | Run `dotnet restore` first, or check your internet connection |

---

## Running the Application

To start the Avalonia desktop application, run:

```bash
dotnet run --project src/SedimentCoreApp.UI
```

### What You Should See

The **Sediment Core Workbench** window will open with:

- A custom **title bar** (no standard Windows/macOS decorations)
- A **header** with tool buttons: File, Home, Analysis, Mapping, Export
- A **menu bar** below the header showing tool-specific actions (changes when you click header buttons)
- A **status bar** at the bottom
- Main content panels (currently placeholder areas for future image display and analysis tools)

The UI uses a modern, Word-like design with smooth animations when switching between tools.

---

## IDE Setup (Optional but Helpful)

### Visual Studio Code

1. Open the repository folder in VS Code:

   ```bash
   code .
   ```

2. Open the **Explorer** view and locate `SedimentCoreApp.sln` or navigate to `src/SedimentCoreApp.UI/`

3. **To run/debug:**
   - Open the **Run and Debug** panel (Ctrl+Shift+D / Cmd+Shift+D)
   - Click **"create a launch.json file"** and select **.NET Core**
   - In `launch.json`, set:

     ```json
     "program": "${workspaceFolder}/src/SedimentCoreApp.UI/bin/Debug/net9.0/SedimentCoreApp.UI.dll",
     "cwd": "${workspaceFolder}/src/SedimentCoreApp.UI"
     ```

   - Press **F5** to start debugging

4. **Avalonia XAML previewer:**
   - Install the **Avalonia for VSCode** extension
   - Open any `.axaml` file and use **Ctrl+Shift+P** → "Avalonia: Preview" to see live XAML preview

---

### JetBrains Rider

1. Open the repository:
   - **File → Open** → Select `SedimentCoreApp.sln`

2. Set the startup project:
   - Right-click `SedimentCoreApp.UI` in the Solution Explorer
   - Select **"Set as Startup Project"** (may be automatic if it's the only executable project)

3. **To run/debug:**
   - Press **F5** or click the **Run** button in the toolbar
   - Rider will automatically detect the Avalonia application

4. **XAML Previewer:**
   - Open any `.axaml` file
   - The Avalonia previewer will appear automatically on the right side
   - You can see live updates as you edit XAML

---

### Visual Studio 2022 (Windows)

1. Open the solution:
   - **File → Open → Project/Solution** → Select `SedimentCoreApp.sln`

2. Set the startup project:
   - Right-click `SedimentCoreApp.UI` in Solution Explorer
   - Select **"Set as Startup Project"**

3. **To run/debug:**
   - Press **F5** or click **Start Debugging**

4. **Avalonia XAML Previewer:**
   - Install the **Avalonia for Visual Studio** extension
   - Open any `.axaml` file
   - The Avalonia previewer will appear in the editor

---

## Making Your First Change (Quick Contribution Exercise)

Let's make a simple change to verify your development environment is working correctly.

### Step 1: Change the Window Title

1. Open `src/SedimentCoreApp.UI/Views/MainWindow.axaml`

2. Find the `Title` property (around line 11):

   ```xml
   Title="Sediment Core Workbench"
   ```

3. Change it to something else:

   ```xml
   Title="Sediment Core Workbench - Development Build"
   ```

4. Save the file

### Step 2: Rebuild and Run

```bash
dotnet build SedimentCoreApp.sln
dotnet run --project src/SedimentCoreApp.UI
```

You should now see your updated window title in the title bar!

### Optional: Try Hot Reload

If you're using an IDE with Avalonia hot reload support (Rider or VS 2022 with Avalonia extension):

1. Run the app in debug mode (F5)
2. Keep the app running
3. Make changes to XAML files
4. Save the file
5. The UI should update automatically without restarting the app (works for most XAML changes)

---

## Next Steps

Now that you have a working development environment, here's where to go next:

### Learn More About the Architecture

- **`docs/architecture/`** (coming soon) – Detailed architectural documentation
  - Project structure and layering principles
  - MVVM pattern usage in the UI
  - How to add new analysis algorithms
  - How to extend the domain model

### Understand the Scientific Methods

- **`science/`** – Scientific background, algorithms, and references
  - Colour space conversions (RGB, Lab, HSV, Munsell)
  - Depth alignment and interpolation methods
  - Statistical analysis techniques (FFT, PCA)

### Contributing Code

When you're ready to contribute:

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the project's layering principles:
   - Data models → `SedimentCore.Domain`
   - Algorithms → `SedimentCore.Analysis`
   - UI components → `SedimentCoreApp.UI`

3. **Test your changes:**

   ```bash
   dotnet build SedimentCoreApp.sln
   dotnet run --project src/SedimentCoreApp.UI
   ```

4. **Commit and push:**

   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub with a clear description of your changes

### Get Help

- Check existing issues on the [GitHub repository](https://github.com/JoshMance/sediment-core-analysis/issues)
- Create a new issue if you encounter problems or have questions
- Review the project README for additional context

---

**Welcome to the project! We look forward to your contributions.** 🎉
