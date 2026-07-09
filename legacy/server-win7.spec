# -*- mode: python ; coding: utf-8 -*-
# 独立服务器程序打包配置（运行库内置，免安装）
# 入口: utils/server.py
#
# 与 Win7 主程序一致：
#   win_private_assemblies=True  -> VC++ / Universal CRT 作为私有程序集打包，目标机免安装
#   upx=False                    -> 关闭压缩，兼容老系统 / 杀毒软件

from PyInstaller.utils.hooks import collect_all

block_cipher = None

app_name = '医保配置服务器'
version = '1.0.0'

a = Analysis(
    ['utils/server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # requests 相关（服务器用 requests 调用自身 API）
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
        # 项目模块
        'config',
        'config.settings',
        'utils',
        'utils.cache',
        'utils.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    # ↓↓↓ 运行库内置，目标机免安装 ↓↓↓
    win_private_assemblies=True,
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
    icon='icon.ico' if __import__('os').path.exists('icon.ico') else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # ↓↓↓ 关闭 UPX，兼容老系统 / 老杀软 ↓↓↓
    upx=False,
    upx_exclude=[],
    # 服务器为常驻进程，保留控制台窗口便于查看日志
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version_info={
        'FileVersion': version,
        'ProductVersion': version,
        'ProductName': app_name,
        'FileDescription': '医保配置服务器',
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
    name=app_name,
)
