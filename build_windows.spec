# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Medical RAG Windows application.

Usage:
    pyinstaller build_windows.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Application metadata
APP_NAME = 'MedicalRAG'
VERSION = '1.0.0'

# Collect all submodules
hiddenimports = [
    # Uvicorn
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
    # Windows-specific
    'win32timezone',
    'winreg',
    # App modules
    'src.user_data',
    'src.desktop_launcher',
    'src.config',
    'src.constants',
    'src.logger',
    'src.pdf_parser',
    'src.chunker',
    'src.vector_db',
    'src.ingestion_progress',
    'src.rag_engine',
    # API modules
    'api.ingest',
    'api.query',
    # Additional dependencies
    'pymupdf4llm',
    'ollama',
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

block_cipher = None

a = Analysis(
    ['windows_launcher.py'],
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
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'tkinter',
        '_tkinter',
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
    exclude_binaries=True,
    name='MedicalRAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Console for error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon file
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
