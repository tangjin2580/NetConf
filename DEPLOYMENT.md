# 服务器部署指南

## 问题说明

如果你遇到 `ModuleNotFoundError: No module named 'config'` 错误，这是因为 Python 模块导入路径问题。

`config.settings` 不是外部依赖包，而是项目内部模块，需要确保从正确的目录运行。

## 解决方案

### 方案 1: 使用 Docker（推荐）

1. **构建镜像**
```bash
docker build -t netconf-server .
```

2. **运行容器**
```bash
docker run -d -p 8080:8080 --name netconf netconf-server
```

3. **查看日志**
```bash
docker logs -f netconf
```

### 方案 2: 直接部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **使用启动脚本运行**
```bash
python start_server.py
```

或者指定端口：
```bash
PORT=4888 python start_server.py
```

### 方案 3: 手动设置 PYTHONPATH

如果必须直接运行某个脚本：

**Linux/Mac:**
```bash
export PYTHONPATH=/app
python utils/server.py
```

**Windows:**
```cmd
set PYTHONPATH=C:\path\to\NetConf
python utils/server.py
```

## 项目结构说明

```
NetConf/
├── config/
│   ├── __init__.py
│   └── settings.py          # 配置文件（不是外部依赖）
├── utils/
│   ├── __init__.py
│   └── server.py            # 服务器模块
├── core/
│   ├── __init__.py
│   ├── hosts.py
│   ├── network.py
│   └── system.py
├── main.py                  # GUI 入口
├── start_server.py          # 服务器启动脚本（新增）
├── requirements.txt         # 外部依赖
├── Dockerfile              # Docker 配置（新增）
└── .dockerignore           # Docker 忽略文件（新增）
```

## 依赖说明

### 外部依赖（需要安装）
- `requests>=2.28.0` - HTTP 请求库
- `Pillow>=9.0.0` - 图像处理库

### 内部模块（无需安装）
- `config.settings` - 项目配置
- `utils.*` - 工具模块
- `core.*` - 核心功能模块

## 验证部署

访问服务器：
```bash
curl http://localhost:8080/api/status
```

应该返回：
```json
{
  "success": true,
  "port": 8080,
  "files_count": 0
}
```

## 常见问题

### Q: 为什么会出现 `ModuleNotFoundError: No module named 'config'`？
A: 因为直接运行子目录中的脚本时，Python 无法找到上级目录的模块。解决方法是：
   1. 使用提供的 `start_server.py` 启动脚本
   2. 或设置 `PYTHONPATH` 环境变量
   3. 或使用 Docker 部署

### Q: requirements.txt 需要包含 config 模块吗？
A: 不需要！`config` 是项目内部模块，不是外部依赖。requirements.txt 只需要包含通过 pip 安装的外部包。

### Q: 如何在服务器上更新配置？
A: 编辑 `config/settings.py` 文件，然后重启服务器。
