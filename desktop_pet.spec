# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Smart Desktop Pet.

Build command: pyinstaller desktop_pet.spec
Output: dist/SmartDesktopPet/ (--onedir mode)
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect PySide6 data files (Qt plugins, platform DLLs, translations)
pyside6_datas = collect_data_files('PySide6', include_py_files=False)
pyside6_binaries = collect_dynamic_libs('PySide6')

# Project assets to bundle
project_datas = [
    ('assets', 'assets'),
    ('data/chat_rules.json', 'data'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=pyside6_datas + project_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
    ],
    excludes=[
        # Large unused PySide6 modules (saves 100+ MB)
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DAnimation',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtHelp',
        'PySide6.QtTest',
        'PySide6.QtDesigner',
        'PySide6.QtShaderTools',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtSpatialAudio',
        'PySide6.QtHttpServer',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtTextToSpeech',
    ],
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
    exclude_binaries=True,  # --onedir mode
    name='SmartDesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # --windowed: no console window
    icon='assets/icon.ico',  # executable icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartDesktopPet',
)
