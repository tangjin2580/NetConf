#!/bin/bash
# 简易启动脚本 - 适用于快速部署

cd "$(dirname "$0")"

echo "🚀 启动 NetConf 配置服务器..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 安装依赖
echo "📦 检查依赖..."
venv/bin/pip install -q -r requirements.txt

# 启动服务器
echo "✅ 启动服务器 (端口: ${PORT:-8080})..."
venv/bin/python start_server.py
