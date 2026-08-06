# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the portable PP-AIPP Windows executable."""

from pathlib import Path

project_root = Path(SPECPATH)
resource_file = project_root / "src" / "pp_aipp" / "resources" / "default.yaml"
font_dir = project_root / "src" / "pp_aipp" / "resources" / "fonts"
brand_dir = project_root / "src" / "pp_aipp" / "resources" / "brand"
local_runner = project_root / "scripts" / "local_ai_runner.py"

a = Analysis(
    [str(project_root / "pp_aipp_desktop_entry.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(resource_file), "pp_aipp/resources"),
        (str(font_dir / "DejaVuSans.ttf"), "pp_aipp/resources/fonts"),
        (str(font_dir / "DejaVuSans-Bold.ttf"), "pp_aipp/resources/fonts"),
        (str(font_dir / "LICENSE-DejaVu.txt"), "pp_aipp/resources/fonts"),
        (str(brand_dir / "cover_b35.png"), "pp_aipp/resources/brand"),
        (str(brand_dir / "collection_opener_b35.png"), "pp_aipp/resources/brand"),
        (str(local_runner), "."),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "openai",
        "openai.resources.images",
    ],
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
