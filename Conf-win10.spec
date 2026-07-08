# -*- mode: python ; coding: utf-8 -*-
# Windows 10/11 (x64) 优化版本打包配置
# Python 3.11 + PyInstaller 6.x
# 支持: Windows 10 1903+, Windows 11
#
# 运行库说明（与 Win7 不同）：
#   Win10/11 系统自带 Universal CRT，且 PyInstaller 会自动收集 vcruntime140/msvcp140，
#   因此无需 win_private_assemblies（该参数已在 PyInstaller 6.0 移除，留着会直接报错）。
#   upx=False 关闭压缩，兼容老杀软。

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
    icon='icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name=f'{app_name}-Win10',
)
