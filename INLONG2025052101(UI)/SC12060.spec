# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\git\\YLong\\INLONG2025052101(UI)\\SC12060.py'],
    pathex=['D:\\git\\YLong\\INLONG2025052101(UI)\\.venv\\Lib\\site-packages'],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5.sip'],
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
    name='SC12060',
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
