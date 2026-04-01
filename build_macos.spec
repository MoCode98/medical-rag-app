# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Medical RAG macOS application.

Usage:
    pyinstaller build_macos.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Application metadata
APP_NAME = 'MedicalRAG'
VERSION = '1.0.0'

# Collect all submodules
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
] + collect_submodules('chromadb') + collect_submodules('fastapi') + collect_submodules('pydantic')

# Collect data files
datas = [
    ('static', 'static'),  # Web UI files
    ('src', 'src'),  # Source code (for imports)
    ('api', 'api'),  # API modules
    ('.env.example', '.'),  # Example config
    ('pdfs', 'pdfs'),  # Bundle PDFs for distribution
]

# Collect data files from packages
datas += collect_data_files('chromadb')
datas += collect_data_files('tiktoken')
datas += collect_data_files('pymupdf')
datas += collect_data_files('pymupdf4llm')

a = Analysis(
    ['macos_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'black',
        'ruff',
        'mypy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MedicalRAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MedicalRAG',
)

app = BUNDLE(
    coll,
    name='MedicalRAG.app',
    icon=None,  # TODO: Add icon file
    bundle_identifier='com.medicalrag.app',
    version=VERSION,
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'LSUIElement': '0',  # Show in Dock
        'CFBundleName': 'Medical RAG',
        'CFBundleDisplayName': 'Medical RAG',
        'CFBundleGetInfoString': 'Medical Research RAG Application',
        'CFBundleIdentifier': 'com.medicalrag.app',
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHumanReadableCopyright': 'Copyright © 2026',
    },
)
