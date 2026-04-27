# Building the Sedivis Installer

## Prerequisites
- [PyInstaller](https://pyinstaller.org): `uv add --dev pyinstaller`
- [Inno Setup](https://jrsoftware.org/isinfo.php): download and install on Windows
- An `.ico` file at `installer/assets/sedivis.ico`
  - Convert `src/ui/resources/logo/logo_dark.png` using an online converter or ImageMagick:
    `magick logo_dark.png -resize 256x256 sedivis.ico`

## Step 1 — Install PyInstaller (first time only)
```
uv add --dev pyinstaller
```

## Step 2 — Bundle the app (PyInstaller)
Run from the project root (~2–5 minutes):
```
uv run pyinstaller installer/Sedivis.spec
```
Output lands in `dist/Sedivis/`. **Test it before continuing:**
```
.\dist\Sedivis\Sedivis.exe
```

## Step 3 — Build the installer (Inno Setup)

## Step 2 — Build the installer (Inno Setup)
Open `installer/setup.iss` in the Inno Setup Compiler and click **Build → Compile**,
or from the command line:
```
iscc installer\setup.iss
```
Output: `dist/installer/Sedivis-0.1.0-Setup.exe`

## Notes
- Bump `AppVersion` in `setup.iss` and `version` in `pyproject.toml` before each release.
- If PyInstaller misses a module, add it to `hiddenimports` in `Sedivis.spec`.
- Always test `dist/Sedivis/Sedivis.exe` on a machine with no Python installed before distributing.
