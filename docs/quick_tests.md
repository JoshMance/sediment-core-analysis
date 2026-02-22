# Quick Tests

Commands to test the demo applications.

## Using uv (Recommended)

```powershell
# Stratigraphy Panel Demo
uv run python src/views/panels/stratigraphy_panel/demo.py

# Image Panel Demo
uv run python src/views/panels/image_panel/demo.py
```

## With Cache Cleanup

```powershell
# Stratigraphy Panel (with cache cleanup)
Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force; uv run python src/views/panels/stratigraphy_panel/demo.py

# Image Panel (with cache cleanup)
Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force; uv run python src/views/panels/image_panel/demo.py
```

## Using Regular Python

After running `pip install -e .`:

```powershell
# Stratigraphy Panel Demo
python src/views/panels/stratigraphy_panel/demo.py

# Image Panel Demo
python src/views/panels/image_panel/demo.py
```

## With Pass/Fail Indicators

```powershell
# Clean and test with visual feedback
Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force; Write-Host "Testing stratigraphy panel..." -ForegroundColor Cyan; uv run python src/views/panels/stratigraphy_panel/demo.py; if ($LASTEXITCODE -eq 0) { Write-Host "✓ Stratigraphy panel demo PASSED" -ForegroundColor Green }

Get-ChildItem -Path "src" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force; Write-Host "Testing image panel..." -ForegroundColor Cyan; uv run python src/views/panels/image_panel/demo.py; if ($LASTEXITCODE -eq 0) { Write-Host "✓ Image panel demo PASSED" -ForegroundColor Green }
```
