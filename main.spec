# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 医保网络配置工具
用于打包main.py为独立exe文件
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('core', 'core'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'config',
        'config.settings',
        'core',
        'core.network',
        'core.hosts',
        'core.system',
        'utils',
        'utils.cache',
        'utils.server',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='医保网络配置工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if __import__('os').path.exists('icon.ico') else None,
)
