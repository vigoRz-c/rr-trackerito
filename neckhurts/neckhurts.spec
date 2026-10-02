# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['neckhurts.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cogs', 'cogs'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'discord',
        'dotenv',
        'aiohttp',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageFilter',
        'utils.image_generator',
        'utils.image_reports_generator',
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
    name='neckhurts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
