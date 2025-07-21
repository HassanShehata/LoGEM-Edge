# logem.spec
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['features/main_ui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('conf/saved_paths.txt', 'conf'),
        ('templates/windows_logon_cef.yaml', 'templates'),
        ('templates/windows_logon_events.yaml', 'templates'),
        ('templates/windows_logon_syslog.yaml', 'templates'),
        ('../models/Qwen3-1.7B-Q3_K_L.gguf', 'models'),  # ← correct relative path
    ],
    hiddenimports=['flet'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='logem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='logem'
)
