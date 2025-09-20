# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['neckhurts.py'],
    pathex=[],
    binaries=[],
    datas=[('les_textes', 'les_textes'), ('.env', '.')],
    hiddenimports=[
        'sous_fonctions.commande_gay', 
        'sous_fonctions.commande_infos', 
        'sous_fonctions.commande_mimic', 
        'sous_fonctions.auto_reponse',
        'les_textes.remplacements_phonetiques',
        'discord',
        'discord.ext.commands',
        'dotenv'
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
