# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Get PyQt5 plugin directories
pyqt_plugins = collect_data_files('PyQt5', include_py_files=False)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        *pyqt_plugins,  # Add PyQt5 plugins
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'PyQt5.QtNetwork',
        'asyncio',
        'python-osc',
        'pythonosc',
        'pythonosc.osc_server',
        'pythonosc.dispatcher',
        'threading',
        'json',
        'websockets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Companion Viewer',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    distpath='output',  # Change output directory
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Companion Viewer',
    distpath='output',  # Change output directory
)
