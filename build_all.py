#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台打包脚本 - 支持 Windows 7/8.1/10/11
使用说明:
    1. 在 Windows 系统上运行此脚本
    2. 确保已安装 Python 3.8+ 
    3. 运行: python build_all.py

作者: Matrix Agent
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# 项目配置
PROJECT_NAME = '医保网络配置工具'
MAIN_SCRIPT = 'main.py'

# 打包输出目录
OUTPUT_DIR = Path('dist')


class BuildConfig:
    """打包配置"""
    def __init__(self, name, spec_file, python_version, description):
        self.name = name
        self.spec_file = spec_file
        self.python_version = python_version
        self.description = description


# 定义多个平台配置
BUILD_CONFIGS = [
    BuildConfig(
        name='Win7-x64',
        spec_file='Conf-win7.spec',
        python_version='3.8',
        description='Windows 7/8.1/10 x64 (推荐旧系统)'
    ),
    BuildConfig(
        name='Win10-x64',
        spec_file='Conf-win10.spec',
        python_version='3.10',
        description='Windows 10/11 x64 (推荐新系统)'
    ),
]


def check_python_version():
    """检查Python版本"""
    print(f"当前 Python 版本: {sys.version}")
    print(f"系统平台: {platform.system()} {platform.release()}")
    print(f"处理器架构: {platform.machine()}")
    print("-" * 50)
    
    if sys.version_info < (3, 8):
        print("错误: 需要 Python 3.8 或更高版本!")
        return False
    return True


def install_dependencies(config_name):
    """安装依赖"""
    print(f"\n{'='*50}")
    print(f"正在安装依赖 ({config_name})...")
    print(f"{'='*50}")
    
    try:
        # 安装兼容版本的依赖
        if 'Win7' in config_name:
            # Win7 需要兼容版本
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                'Pillow>=9.0.0,<10.0.0',
                'requests>=2.28.0,<3.0.0',
                'pyinstaller>=5.13.0,<6.0.0',
            ])
        else:
            # Win10+ 使用最新版
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                '-r', 'requirements.txt'
            ])
        print("依赖安装完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False


def build_spec(spec_file, output_name):
    """使用PyInstaller构建spec文件"""
    print(f"\n{'='*50}")
    print(f"正在构建: {output_name}")
    print(f"使用配置文件: {spec_file}")
    print(f"{'='*50}")
    
    # 清理旧的构建
    build_dir = Path('build')
    if build_dir.exists():
        print("清理旧的build目录...")
        shutil.rmtree(build_dir)
    
    try:
        # 运行PyInstaller
        cmd = ['pyinstaller', spec_file, '--noconfirm']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"构建失败: {result.stderr}")
            return False
        
        print(f"构建成功: {output_name}")
        
        # 重命名输出目录
        dist_dir = OUTPUT_DIR / f'{PROJECT_NAME}-{output_name}'
        old_dir = OUTPUT_DIR / '医保网络配置工具'
        
        if old_dir.exists() and not dist_dir.exists():
            shutil.move(str(old_dir), str(dist_dir))
        
        return True
        
    except Exception as e:
        print(f"构建过程出错: {e}")
        return False


def create_launcher_bat(output_dir, config_name):
    """创建简单的启动器批处理文件"""
    launcher_content = f'''@echo off
chcp 65001 > nul
echo ========================================
echo   {PROJECT_NAME} - {config_name}
echo ========================================
echo.
echo 正在启动程序...
echo.
cd /d "%~dp0"
start "" "%~dp0{PROJECT_NAME}.exe"
'''
    
    launcher_path = output_dir / '启动工具.bat'
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print(f"已创建启动器: {launcher_path}")


def create_vcredist_bat(output_dir):
    """创建VC++运行库安装提示批处理"""
    content = '''@echo off
chcp 65001 > nul
echo ========================================
echo   Visual C++ 运行库安装
echo ========================================
echo.
echo 如果程序无法运行，请安装以下运行库:
echo.
echo 下载地址:
echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
echo   https://aka.ms/vs/17/release/vc_redist.x86.exe
echo.
echo 直链下载:
echo   x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
echo   x86: https://aka.ms/vs/17/release/vc_redist.x86.exe
echo.
pause
'''
    
    vcredist_path = output_dir / '安装运行库.bat'
    with open(vcredist_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建VC++安装提示: {vcredist_path}")


def create_readme(output_dir, config_name):
    """创建说明文件"""
    content = f'''# {PROJECT_NAME}
## 版本: {config_name}

### 系统要求
- 最低: Windows 7 SP1 (KB2533623更新)
- 推荐: Windows 10 1903 或更高版本

### 包含内容
- 应用程序主程序
- 所有必要的运行库
- 本说明文件

### 安装说明
1. 解压到任意目录
2. 双击运行 "{PROJECT_NAME}.exe"
3. 如遇运行错误，请先安装 "安装运行库.bat" 中的 Visual C++ 运行库

### 下载运行库
x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
x86: https://aka.ms/vs/17/release/vc_redist.x86.exe

### 常见问题
Q: 提示缺少DLL?
A: 请安装上方提供的Visual C++运行库

Q: Windows 7 无法运行?
A: 请确保系统已安装 KB2533623 更新
   下载地址: https://www.microsoft.com/zh-cn/download/details.aspx?id=26764

---
生成时间: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}
'''
    
    readme_path = output_dir / 'README.txt'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建说明文件: {readme_path}")


def build_all():
    """构建所有平台版本"""
    print("\n" + "=" * 60)
    print(f"  {PROJECT_NAME} 多平台打包工具")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 构建每个配置
    success_count = 0
    for config in BUILD_CONFIGS:
        # 检查spec文件是否存在
        if not Path(config.spec_file).exists():
            print(f"\n警告: 配置文件 {config.spec_file} 不存在，跳过...")
            continue
        
        # 安装依赖
        if not install_dependencies(config.name):
            print(f"依赖安装失败，跳过 {config.name}")
            continue
        
        # 构建
        if build_spec(config.spec_file, config.name):
            dist_dir = OUTPUT_DIR / f'{PROJECT_NAME}-{config.name}'
            if dist_dir.exists():
                create_launcher_bat(dist_dir, config.name)
                create_vcredist_bat(dist_dir)
                create_readme(dist_dir, config.name)
            success_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("  打包完成!")
    print("=" * 60)
    print(f"\n成功: {success_count}/{len(BUILD_CONFIGS)}")
    print(f"\n输出目录: {OUTPUT_DIR.absolute()}")
    
    if success_count > 0:
        print("\n生成的文件:")
        for item in OUTPUT_DIR.iterdir():
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                print(f"  - {item.name}/ ({size // (1024*1024)} MB)")


def build_single(config_name):
    """构建单个配置"""
    for config in BUILD_CONFIGS:
        if config.name == config_name:
            if not install_dependencies(config.name):
                return False
            return build_spec(config.spec_file, config.name)
    print(f"未找到配置: {config_name}")
    return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 单个配置构建
        config_name = sys.argv[1]
        build_single(config_name)
    else:
        # 构建所有配置
        build_all()
