#!/usr/bin/env python3
"""
服务器启动脚本
确保从项目根目录启动，解决模块导入问题
"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并启动服务器
from utils.server import InfoServer

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = InfoServer(port=port)
    print(f"正在启动信息服务器，端口: {port}")
    print(f"项目根目录: {project_root}")
    server.start()
