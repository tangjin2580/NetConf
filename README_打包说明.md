# 医保网络配置工具 - 多平台打包说明

## 概述

本项目支持为不同的 Windows 版本创建兼容的安装包:

| 打包版本 | Python版本 | PyInstaller版本 | 支持系统 | 推荐场景 |
|---------|-----------|----------------|---------|---------|
| **Win7-x64** | 3.8 | 5.13 | Windows 7 SP1+ | 旧电脑、Win7系统 |
| **Win10-x64** | 3.10 | 6.x | Windows 10 1903+ | 新电脑、Win10/11 |

---

## 快速开始

### 方法一: 一键打包 (推荐)

```batch
# 在 Windows 系统中双击运行，或在命令提示符中执行:
python build_all.py
```

这将自动:
1. 安装必要的依赖
2. 构建 Win7-x64 和 Win10-x64 两个版本
3. 在 `dist/` 目录生成打包文件

### 方法二: 单独打包

```batch
# 只打包 Win7 版本
python build_all.py Win7-x64

# 只打包 Win10 版本  
python build_all.py Win10-x64
```

---

## 手动打包步骤

如果你需要更精细的控制，可以手动执行以下步骤:

### 1. 安装 Python 3.8 (Win7兼容)

**下载地址:**
- Python 3.8.x: https://www.python.org/downloads/release/python-3818/
- **重要**: 安装时勾选 "Add Python to PATH"

### 2. 创建虚拟环境

```batch
# 使用 Python 3.8 创建虚拟环境
python3.8 -m venv venv_win7

# 激活虚拟环境
venv_win7\Scripts\activate
```

### 3. 安装依赖

```batch
# Win7 版本
pip install Pillow>=9.0.0,<10.0.0
pip install requests>=2.28.0,<3.0.0
pip install pyinstaller>=5.13.0,<6.0.0

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 4. 运行打包

```batch
# Win7 版本
pyinstaller Conf-win7.spec --noconfirm

# Win10 版本
pyinstaller Conf-win10.spec --noconfirm
```

### 5. 找到打包结果

打包结果在 `dist/` 目录:
```
dist/
├── 医保网络配置工具-Win7-x64/
│   ├── 医保网络配置工具.exe
│   └── ...
└── 医保网络配置工具-Win10-x64/
    ├── 医保网络配置工具.exe
    └── ...
```

---

## Windows 7 用户注意事项

### 1. 必须安装 KB2533623 更新

Windows 7 SP1 必须安装此更新才能运行某些程序:

**下载地址:** https://www.microsoft.com/zh-cn/download/details.aspx?id=26764

### 2. 安装 Visual C++ 运行库

如果程序提示缺少 DLL，请安装:

- **x64**: https://aka.ms/vs/17/release/vc_redist.x64.exe
- **x86**: https://aka.ms/vs/17/release/vc_redist.x86.exe

### 3. 分发建议

建议将以下文件一起分发:
```
医保网络配置工具-Win7-x64/
├── 医保网络配置工具.exe     # 主程序
├── vcruntime140.dll         # VC++运行库 (从打包中获取)
├── msvcp140.dll             # 同上
└── 安装运行库.bat            # 运行库安装提示
```

---

## 故障排除

### 错误: "api-ms-win-*.dll 缺失"

**原因:** Windows 7 缺少必要的系统更新

**解决方案:**
1. 安装 KB2533623 更新
2. 或从其他 Windows 10/11 系统复制相关 DLL 到程序目录

### 错误: "不是有效的 Win32 程序"

**原因:** 可能下载了 32 位程序但系统是 64 位，或相反

**解决方案:**
- 确认下载的是正确的架构版本

### 错误: "Python 版本不兼容"

**原因:** Python 3.10+ 不再支持 Windows 7

**解决方案:**
- 使用 Python 3.8 重新打包

### 错误: "ImportError: DLL load failed"

**原因:** 缺少 Visual C++ 运行库

**解决方案:**
安装 VC++ 2015-2022 运行库 (见上方链接)

---

## 版本兼容性对照表

```
┌─────────────────────────────────────────────────────────────┐
│                     Python 版本兼容性                        │
├──────────────┬─────────────────────────────────────────────┤
│ Python 3.6   │ Windows Vista, 7, 8.1, 10                   │
│ Python 3.7   │ Windows 7, 8.1, 10                          │
│ Python 3.8   │ Windows 7, 8.1, 10, 11 ✓ Win7 最后支持版本  │
│ Python 3.9   │ Windows 8.1, 10, 11                          │
│ Python 3.10+ │ Windows 10, 11                              │
└──────────────┴─────────────────────────────────────────────┘
```

---

## 技术支持

如遇到问题，请提供:
1. Windows 版本 (winver)
2. 错误截图或错误信息
3. 使用的打包版本 (Win7-x64 或 Win10-x64)

---

**生成时间:** 2024
