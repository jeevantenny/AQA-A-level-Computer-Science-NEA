# -*- mode: python ; coding: utf-8 -*-


_c_path_list = [
    "assets/anim_controllers",
    "assets/animations",
    "assets/audio",
    "assets/fonts"
]


a = Analysis(
    ['__main__.py'],
    pathex=[],
    binaries=[],
    datas=None,
    hiddenimports=[],
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
    name='__main__',
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
