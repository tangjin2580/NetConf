#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包前依赖测试脚本
运行此脚本确保所有依赖正常后再打包
"""

import subprocess
import sys

def check_package(package):
    """检查包是否可用"""
    try:
        __import__(package)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    print("=" * 50)
    print("依赖检查工具")
    print("=" * 50)
    
    # 检查必要包
    required = {
        'requests': 'HTTP请求库',
        'Pillow': '图片处理库',
    }
    
    all_ok = True
    for package, desc in required.items():
        ok, error = check_package(package)
        status = "✓" if ok else "✗"
        print(f"{status} {package} ({desc}): {'已安装' if ok else f'缺失 - {error}'}")
        if not ok:
            all_ok = False
    
    print("=" * 50)
    
    if not all_ok:
        print("❌ 依赖检查失败，请先安装缺失的包")
        print(f"运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 所有依赖检查通过！")
    print("\n下一步可以打包：")
    print("pyinstaller --onefile Conf.py")
    
    # 尝试导入项目模块
    print("\n测试导入项目模块...")
    try:
        import Conf
        print("✓ Conf.py 导入成功")
    except Exception as e:
        print(f"✗ Conf.py 导入失败: {e}")
        all_ok = False
    
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
