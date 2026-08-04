# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the portable PP-AIPP Windows executable."""

from pathlib import Path

project_root = Path(SPECPATH)
resource_file = project_root / "src" / "pp_aipp" / "resources" / "default.yaml"

a = Analysis(
    [str(project_root / "pp_aipp_desktop_entry.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[(str(resource_file), "pp_aipp/resources")],
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PP-AIPP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
