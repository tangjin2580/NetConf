# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

a = Analysis(
    ['Conf.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # requests 相关
        'requests',
        'requests.adapters',
        'requests.api',
        'requests.auth',
        'requests.compat',
        'requests.cookies',
        'requests.exceptions',
        'requests.hooks',
        'requests.models',
        'requests.sessions',
        'requests.status_codes',
        'requests.structures',
        'requests.utils',
        'charset_normalizer',
        'charset_normalizer.__init__',
        'charset_normalizer.utils',
        'charset_normalizer.mappings',
        'idna',
        'idna.core',
        'idna.uts46',
        'urllib3',
        'urllib3.util',
        'urllib3.exceptions',
        'urllib3.response',
        'urllib3.poolmanager',
        'certifi',
        'openssl',
        # Pillow 相关
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin',
        'PIL.BmpImagePlugin',
        'PIL.GifImagePlugin',
        'PIL.ImageFont',
        'PIL.ImageDraw',
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
    name='医保网络配置工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    windowed=True,
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
    name='医保网络配置工具',
)
