# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Add runtime hook for error logging
with open('error_hook.py', 'w') as f:
    f.write('''
import sys
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    print(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    with open('error_log.txt', 'a') as f:
        f.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception
''')

# Check if icon exists
icon_file = 'icon.ico' if os.path.exists('icon.ico') else None
icon_data = [('icon.ico', '.')] if icon_file else []

# Get all PyQt5 plugins and modules
pyqt_plugins = collect_data_files('PyQt5', include_py_files=True)
pyqt_modules = collect_submodules('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *icon_data,  # Add icon only if it exists
        ('sounds/warning1.wav', 'sounds'),
        ('sounds/warning2.wav', 'sounds'),
        ('sounds/warning3.wav', 'sounds'),
        ('sounds/end1.wav', 'sounds'),
        ('sounds/end2.wav', 'sounds'),
        ('sounds/end3.wav', 'sounds'),
        *pyqt_plugins,  # Add PyQt5 plugins
    ],
    hiddenimports=[
        *pyqt_modules,  # Add all PyQt5 modules
        'asyncio',
        'pythonosc',
        'pythonosc.osc_server',
        'pythonosc.dispatcher',
        'threading',
        'json',
        'websockets',
        'winsound',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['error_hook.py'],  # Add error logging hook
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
    console=True,  # Enable console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file  # Use icon only if it exists
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
