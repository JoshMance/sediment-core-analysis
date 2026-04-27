# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Sedivis
# Run from the project root: uv run pyinstaller installer/Sedivis.spec

import sys
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        *copy_metadata('imageio'),
        (str(ROOT / 'src' / 'science' / 'data'), 'src/science/data'),
        (str(ROOT / 'src' / 'ui' / 'resources' / 'icons'), 'src/ui/resources/icons'),
        (str(ROOT / 'src' / 'ui' / 'resources' / 'logo'), 'src/ui/resources/logo'),
        (str(ROOT / 'src' / 'ui' / 'resources' / 'theme'), 'src/ui/resources/theme'),
        # Package metadata required by imageio (and potentially others) at runtime
        (str(ROOT / '.venv' / 'Lib' / 'site-packages' / 'imageio-*.dist-info'), 'imageio-0.dist-info'),
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'PySide6.QtXml',
        'PySide6.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sedivis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'installer' / 'assets' / 'sedivis.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sedivis',
)
