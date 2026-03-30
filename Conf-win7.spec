# -*- mode: python ; coding: utf-8 -*-
# Windows 7 x64/x86 兼容版本打包配置
# Python 3.8 + PyInstaller 5.13
# 支持: Windows 7 SP1+, Windows 8.1, Windows 10/11

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

# Windows兼容性Manifest - 支持 Win7 及以上
win_manifest = '''
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
        <application>
            <!-- Windows 7 -->
            <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
            <!-- Windows 8 -->
            <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
            <!-- Windows 8.1 -->
            <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
            <!-- Windows 10 -->
            <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
        </application>
    </compatibility>
    <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
        <security>
            <requestedPrivileges>
                <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
            </requestedPrivileges>
        </security>
    </trustInfo>
</assembly>
'''

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
    manifest=win_manifest,
    # 嵌入版本信息
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
    name=f'{app_name}-Win7-x64',
)
