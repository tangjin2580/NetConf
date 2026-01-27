# 医保网络配置工具

现代化的医保网络配置工具，支持双WAN配置、单机配置、网络检测等功能。

## 📁 项目结构

```
NetConf/
├── main.py                    # 主入口文件（原Conf.py）
├── config/                    # 配置模块
│   ├── __init__.py
│   └── settings.py            # 配置常量（服务器、hosts条目等）
├── core/                      # 核心业务模块
│   ├── __init__.py
│   ├── network.py             # 网络工具（IP、MTU、路由、ping等）
│   ├── hosts.py               # Hosts文件管理
│   └── system.py              # 系统检查（管理员权限、向日葵等）
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── cache.py               # 缓存管理
│   └── server.py              # 服务器通信（含在线编辑功能）
├── cache/                     # 缓存目录
├── info/                      # 信息存储目录
├── server.py                  # HTTP服务器独立启动脚本
├── requirements.txt           # 依赖列表
├── Conf.py                    # 旧版主文件（保留备份）
└── Conf.py.backup            # 原始备份
```

## ✨ 主要功能

### 1. 🔍 医保网络检测
- Ping 10.35.128.1（医保网关）
- 检测两定系统（hisips.shx.hsip.gov.cn）
- 检测费用监管系统（fms.shx.hsip.gov.cn）
- 检测综合服务系统（cts-svc.shx.hsip.gov.cn）

### 2. 🌐 双WAN配置（路由器）
- 向日葵远程协助
- 路由器账号配置
- MTU一键设置（1300）
- 单路由配置信息返回
- 配置信息展示（从服务器获取）

### 3. 💻 单机配置（直连）
- 仅补全 hosts 文件
- IP / MTU / 路由完整配置
- 配置验证和连通性测试

### 4. 📡 服务器功能（新增）
- 文件管理（上传、下载）
- **在线编辑txt/md/log等文本文件**
- 自动识别可编辑文件类型
- Web界面管理

## 🚀 运行方式

### Windows（需要管理员权限）
```bash
# 右键点击 main.py -> 以管理员身份运行
# 或在管理员CMD/PowerShell中运行：
python main.py
```

### 启动HTTP服务器（支持在线编辑）
```bash
python server.py
# 默认端口: 8080
# 访问: http://localhost:8080
# 默认账号: info / 密码: mecPassw0rd
```

**server.py 功能特性：**
- ✅ 文件上传/下载
- ✅ 在线编辑 txt/md/log/json/xml 等文本文件
- ✅ 实时保存修改
- ✅ 文件管理（删除、查看）
- ✅ 漂亮的Web界面

## 📦 依赖安装

```bash
pip install -r requirements.txt
```

主要依赖：
- tkinter（GUI）
- Pillow（图片处理）
- requests（HTTP请求）

## 🔧 打包说明

使用 PyInstaller 打包时注意：
1. 确保所有模块正确导入
2. 添加 `--hidden-import` 参数包含所有子模块
3. 使用 `--add-data` 包含配置文件

示例命令：
```bash
pyinstaller --onefile --windowed \
  --hidden-import=config.settings \
  --hidden-import=core.network \
  --hidden-import=core.hosts \
  --hidden-import=core.system \
  --hidden-import=utils.cache \
  --hidden-import=utils.server \
  --name="医保网络配置工具" \
  main.py
```

## 🎯 重构说明

**v2.0 重构（2026-01-27）**
- ✅ 代码减少 35.3%（58043 → 37579 字符）
- ✅ 模块化架构（config / core / utils）
- ✅ 主文件更名为 main.py
- ✅ 新增在线编辑txt文件功能
- ✅ 完善的目录结构和文档

**模块分类：**
- `config/` - 配置常量（服务器、hosts、网络参数等）
- `core/` - 核心业务（网络操作、hosts管理、系统检查）
- `utils/` - 工具函数（缓存、服务器通信）

## 📝 更新日志

- **2026-01-27**: v2.0 大重构，模块化架构，增加在线编辑功能
- **2026-01-27**: 增加医保网络检测功能
- **2026-01-27**: 增加单路由配置返回
- **2026-01-27**: 所有页面增加返回上级菜单功能

## 👨‍💻 开发者

- 医保网络配置工具团队
