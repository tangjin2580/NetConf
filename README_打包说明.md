# 医保网络配置工具 - 多平台打包说明

## 概述

本项目支持为不同的 Windows 版本创建兼容的安装包:

| 打包版本 | Python版本 | PyInstaller版本 | 支持系统 | 推荐场景 |
|---------|-----------|----------------|---------|---------|
| **Win7-x64** | 3.8 | 5.13 | Windows 7 SP1+ (64位) | 旧电脑、Win7系统 |
| **Win10-x64** | 3.10/3.11 | 6.x | Windows 10 1903+ | 新电脑、Win10/11 |

> **重要**: 所有版本均已将 Visual C++ 运行库与 Universal CRT 打包进程序，
> 客户机**无需安装任何运行库**，解压后直接双击即可运行。

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
# Win7 版本（x64，运行库内置，免安装）
pyinstaller Conf-win7.spec --noconfirm
```

### 5. 找到打包结果

打包结果在 `dist/` 目录:
```
dist/
└── 医保网络配置工具-Win7/   # 64位，运行库已内置
    ├── 医保网络配置工具.exe
    ├── vcruntime140.dll / msvcp140.dll / ucrtbase.dll ...
    ├── api-ms-win-crt-*.dll ...
    └── 运行库已内置-无需安装.txt
```

---

## Windows 7 用户注意事项（运行库已内置，免安装）

> 新版本的 Win7 打包已通过 `win_private_assemblies=True` 把 **Visual C++ 运行库** 与
> **Universal CRT（api-ms-win-crt-*.dll / ucrtbase.dll）** 一并打进程序目录，
> 客户机**无需安装任何运行库**即可直接运行。以下仅作为极端老系统的兜底参考。

### 1. 确认系统为 64 位

本版本为 64 位程序，请确认客户机为 64 位系统（右键「计算机」→ 属性查看）。
32 位系统不在支持范围内。

### 2. 兜底：极少数未打 SP1 的老系统

若解压后仍提示缺少 dll，多为 Windows 7 未装 SP1 或缺少系统更新，可离线安装（无需联网升级）：
- **KB2533623**: https://www.microsoft.com/zh-cn/download/details.aspx?id=26764
- **Windows 7 SP1 离线包**: https://www.catalog.update.microsoft.com/ （搜索 KB976932）

### 3. 分发建议

直接把对应 zip 解压后整体拷贝给客户即可，目录示例如下（运行库已包含在内）:
```
医保网络配置工具-Win7/
├── 医保网络配置工具.exe        # 主程序
├── vcruntime140.dll / msvcp140.dll / ucrtbase.dll ...  # 运行库（已内置）
├── api-ms-win-crt-*.dll ...    # Universal CRT（已内置）
└── 运行库已内置-无需安装.txt     # 说明
```

---

## 故障排除

### 错误: "api-ms-win-*.dll 缺失"

**原因:** Windows 7 缺少必要的系统更新

**解决方案:**
1. 确认客户机为 64 位系统（本版本仅 64 位）
2. 新版本已内置 Universal CRT，如仍缺失，给老系统离线安装 KB2533623 + SP1

### 错误: "不是有效的 Win32 程序"

**原因:** 本版本为 64 位，放到 32 位系统无法运行

**解决方案:**
- 确认客户机为 64 位系统（右键「计算机」→ 属性查看）

### 错误: "Python 版本不兼容"

**原因:** Python 3.10+ 不再支持 Windows 7

**解决方案:**
- 使用 Python 3.8 重新打包（CI 已自动处理）

### 错误: "ImportError: DLL load failed" / "由于找不到 VCRUNTIME140.dll"

**原因:** 旧版打包依赖系统全局 VC++ 运行库，老电脑未安装

**解决方案:**
- 使用新版本（已 `win_private_assemblies=True`，运行库随包内置，无需安装）

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
1. Windows 版本 (winver) 及位数（确认是 64 位）
2. 错误截图或错误信息
3. 使用的打包版本 (Win7-x64 / Win10-x64)

---

**生成时间:** 2024
