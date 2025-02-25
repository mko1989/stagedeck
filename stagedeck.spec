# -*- mode: python ; coding: utf-8 -*-
import os
<<<<<<< HEAD
import sys
=======
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

<<<<<<< HEAD
# Check if we're on macOS
is_mac = sys.platform == 'darwin'

# Get icon based on platform
if is_mac:
    icon_file = 'icon.icns' if os.path.exists('icon.icns') else None
else:
    icon_file = 'icon.ico' if os.path.exists('icon.ico') else None
=======
# Check if icon exists
icon_file = 'icon.ico' if os.path.exists('icon.ico') else None
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9

# Get PyQt5 plugins
pyqt_plugins = collect_data_files('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sounds/*', 'sounds'),
        ('web_server.py', '.'),
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
        'pygame',
        'pygame.mixer',
        'pygame.mixer_music',
        'fastapi',
        'uvicorn',
        'PIL',
        'numpy',
        'cv2',
        'multipart',
        'aiofiles',
        'fastapi.responses',
        'fastapi.staticfiles',
        'fastapi.websockets',
        'uvicorn.config',
        'uvicorn.main',
        'uvicorn.loops',
        'uvicorn.protocols',
        'uvicorn.lifespan',
        'uvicorn.logging',
        'starlette',
        'starlette.routing',
        'starlette.applications',
        'starlette.responses',
        'starlette.websockets',
        'starlette.types',
        'starlette.datastructures',
        'starlette.staticfiles',
        'web_server'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
<<<<<<< HEAD
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
=======
    noarchive=False
)

pyz = PYZ(a.pure, cipher=block_cipher)
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StageDeck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
<<<<<<< HEAD
    console=False,
=======
    console=True,  # Set this to False to hide the console window
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file
)

<<<<<<< HEAD
# For macOS, create a .app bundle
if is_mac:
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='StageDeck.app',
        icon=icon_file,
        bundle_identifier='com.stagedeck.app',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHighResolutionCapable': True,
            'NSMicrophoneUsageDescription': 'StageDeck needs access to the microphone for audio features.',
            'NSCameraUsageDescription': 'StageDeck needs access to the camera for video features.',
        }
    )
else:
    # For Windows, create a directory with all files
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='StageDeck',
    )
=======
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
>>>>>>> c0b2564a41945d9df9eb14ab6dfef9dbfc1de4a9
