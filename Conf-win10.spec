# -*- mode: python ; coding: utf-8 -*-
# Windows 10/11 x64/x86 优化版本打包配置
# Python 3.9/3.10 + PyInstaller 6.x
# 支持: Windows 10 1903+, Windows 11

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 基础配置
app_name = '医保网络配置工具'
version = '1.0.0'

a = Analysis(
    ['main.py'],
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
        # 项目模块
        'config',
        'config.settings',
        'core',
        'core.network',
        'core.hosts',
        'core.system',
        'utils',
        'utils.cache',
        'utils.server',
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
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version_info={
        'FileVersion': version,
        'ProductVersion': version,
        'ProductName': app_name,
        'FileDescription': '医保网络配置工具',
        'LegalCopyright': 'Copyright 2024',
    },
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=f'{app_name}-Win10-x64',
)
