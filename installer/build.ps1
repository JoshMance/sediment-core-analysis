# Sedivis build script
# Run from anywhere:
#   .\installer\build.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

Set-Location $RepoRoot

function Find-Iscc {
    $isccOnPath = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($isccOnPath) {
        return $isccOnPath.Source
    }

    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\iscc.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Ensure-InnoSetup {
    $iscc = Find-Iscc
    if ($iscc) {
        return $iscc
    }

    Write-Host "Inno Setup not found. Attempting automatic install via winget..." -ForegroundColor Yellow

    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Inno Setup is missing and winget is unavailable. Install Inno Setup manually from https://jrsoftware.org/isinfo.php"
    }

    & winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "winget returned a non-zero exit code. Re-checking for iscc.exe..." -ForegroundColor Yellow
    }

    $iscc = Find-Iscc
    if (-not $iscc) {
        throw "Inno Setup appears installed but iscc.exe was not found. Reopen terminal and try again."
    }

    return $iscc
}

function Ensure-LicenseFile {
    $licenseSrc = Join-Path $RepoRoot "LICENSE"
    $licenseDst = Join-Path $RepoRoot "installer\assets\license.txt"

    if (-not (Test-Path $licenseDst)) {
        if (-not (Test-Path $licenseSrc)) {
            throw "Missing LICENSE at repo root, required to generate installer/assets/license.txt"
        }
        Copy-Item $licenseSrc $licenseDst -Force
    }
}

Write-Host "==> Step 1: Ensure installer prerequisites..." -ForegroundColor Cyan
Ensure-LicenseFile
$iscc = Ensure-InnoSetup

Write-Host ""
Write-Host "==> Step 2: Bundling with PyInstaller..." -ForegroundColor Cyan
uv run pyinstaller installer/Sedivis.spec --noconfirm

Write-Host ""
Write-Host "==> Step 3: Compiling installer with Inno Setup..." -ForegroundColor Cyan
& $iscc installer\setup.iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed."
}

Write-Host ""
Write-Host "==> Done! Installer at: dist\installer\Sedivis-0.1.0-Setup.exe" -ForegroundColor Green
