# -*- mode: python ; coding: utf-8 -*-
# waypoint-onedir.spec - Folder-based build (no _MEI* temp extraction)

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('config.yaml', '.'), ('modern-ui.html', '.'), ('assets', 'assets')],
    hiddenimports=['yaml', 'schedule', 'github', 'packaging', 'requests', 'urllib3', 'extensions', 'playwright'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# ONEDIR: Creates a folder with all files pre-extracted
# No temp extraction at runtime = no _MEI* conflicts
exe = EXE(
    pyz,
    a.scripts,
    [],  # Empty - binaries/datas go to COLLECT, not EXE
    exclude_binaries=True,  # Key difference for onedir
    name='waypoint',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)

# COLLECT: Gathers all files into the output folder
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='waypoint',  # Output folder name
)
