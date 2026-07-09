#!/bin/bash
# NetConf 服务器部署脚本

set -e

echo "================================"
echo "NetConf 配置服务器 - 部署脚本"
echo "================================"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 配置变量
PROJECT_DIR="/opt/netconf"
SERVICE_NAME="netconf-server"
LOG_DIR="/var/log/netconf"

echo ""
echo "步骤 1/6: 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

echo ""
echo "步骤 2/6: 安装系统依赖..."
# Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip python3-venv git
# CentOS/RHEL
elif command -v yum &> /dev/null; then
    yum install -y python3 python3-pip git
fi

echo ""
echo "步骤 3/6: 克隆/更新代码..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone git@github.com:tangjin2580/NetConf.git .
fi

echo ""
echo "步骤 4/6: 创建虚拟环境并安装依赖..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "步骤 5/6: 配置系统服务..."
# 修改服务文件中的路径
sed -i "s|/path/to/NetConf|$PROJECT_DIR|g" netconf-server.service
# 复制服务文件
cp netconf-server.service /etc/systemd/system/$SERVICE_NAME.service
# 创建日志目录
mkdir -p $LOG_DIR
chmod 755 $LOG_DIR

echo ""
echo "步骤 6/6: 启动服务..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo ""
echo "================================"
echo "✅ 部署完成！"
echo "================================"
echo ""
echo "📋 服务管理命令："
echo "  启动服务: systemctl start $SERVICE_NAME"
echo "  停止服务: systemctl stop $SERVICE_NAME"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo "🌐 访问地址: http://服务器IP:8080"
echo "🔐 认证信息: 用户名 info / 密码 mecPassw0rd"
echo ""
