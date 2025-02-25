# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Check if icon exists
icon_file = 'icon.ico' if os.path.exists('icon.ico') else None

# Get PyQt5 plugins
pyqt_plugins = collect_data_files('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sounds/warning1.wav', 'sounds'),
        ('sounds/warning2.wav', 'sounds'),
        ('sounds/warning3.wav', 'sounds'),
        ('sounds/end1.wav', 'sounds'),
        ('sounds/end2.wav', 'sounds'),
        ('sounds/end3.wav', 'sounds'),
        *pyqt_plugins,
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'PyQt5.QtNetwork',
        'asyncio',
        'pythonosc',
        'pythonosc.osc_server',
        'pythonosc.dispatcher',
        'threading',
        'json',
        'websockets',
        'winsound',
        'fastapi',
        'uvicorn',
        'PIL',
        'numpy',
        'cv2',
        'multipart',
        'aiofiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StageDeck',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StageDeck'
)
