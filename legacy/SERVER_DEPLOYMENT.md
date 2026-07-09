# 服务器部署指南

## 📋 部署要求

- **操作系统**: Linux (Ubuntu/Debian/CentOS)
- **Python**: 3.7+
- **端口**: 8080 (可通过环境变量 `PORT` 修改)
- **权限**: 需要管理员权限进行系统服务配置

---

## 🚀 快速部署方式

### 方式1：一键部署（systemd 服务）

适合生产环境，服务自动启动、崩溃自动重启。

```bash
# 1. 下载部署脚本
wget https://raw.githubusercontent.com/tangjin2580/NetConf/main/deploy.sh
chmod +x deploy.sh

# 2. 执行部署（需要 root 权限）
sudo ./deploy.sh
```

**服务管理命令**：
```bash
sudo systemctl start netconf-server    # 启动
sudo systemctl stop netconf-server     # 停止
sudo systemctl restart netconf-server  # 重启
sudo systemctl status netconf-server   # 状态
journalctl -u netconf-server -f        # 查看日志
```

---

### 方式2：简易启动（测试环境）

适合快速测试，不需要 root 权限。

```bash
# 1. 克隆代码
git clone git@github.com:tangjin2580/NetConf.git
cd NetConf

# 2. 赋予执行权限
chmod +x run.sh

# 3. 启动服务器
./run.sh
```

---

### 方式3：Docker 部署

```bash
# 1. 构建镜像
docker build -t netconf-server .

# 2. 运行容器
docker run -d \
  --name netconf \
  -p 8080:8080 \
  --restart always \
  netconf-server

# 3. 查看日志
docker logs -f netconf
```

---

### 方式4：后台运行（nohup）

```bash
cd /path/to/NetConf

# 后台运行
nohup venv/bin/python start_server.py > server.log 2>&1 &

# 停止服务
ps aux | grep start_server.py
kill <PID>
```

---

### 方式5：使用 Supervisor

```bash
# 1. 安装 supervisor
sudo apt-get install supervisor  # Ubuntu/Debian
# 或
sudo yum install supervisor       # CentOS

# 2. 创建配置文件
sudo nano /etc/supervisor/conf.d/netconf.conf
```

配置内容：
```ini
[program:netconf]
command=/opt/netconf/venv/bin/python /opt/netconf/start_server.py
directory=/opt/netconf
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/netconf/server.log
```

```bash
# 3. 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start netconf
```

---

## 🔧 配置说明

### 修改端口

方法1: 环境变量
```bash
export PORT=9000
./run.sh
```

方法2: 修改 systemd 服务文件
```bash
sudo nano /etc/systemd/system/netconf-server.service
# 修改 Environment="PORT=9000"
sudo systemctl daemon-reload
sudo systemctl restart netconf-server
```

### 修改认证密码

编辑 `config/settings.py`:
```python
SERVER_USERNAME = "your_username"
SERVER_PASSWORD = "your_password"
```

---

## 🌐 访问配置

### 本地访问
```
http://localhost:8080
```

### 远程访问
```
http://服务器IP:8080
```

### 配置 Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔐 安全建议

1. **修改默认密码**：部署后立即修改 `config/settings.py` 中的密码
2. **配置防火墙**：只开放必要的端口
   ```bash
   sudo ufw allow 8080/tcp
   sudo ufw enable
   ```
3. **使用 HTTPS**：建议使用 Nginx + Let's Encrypt 配置 SSL
4. **限制访问 IP**：在 Nginx 中配置白名单

---

## 🐛 故障排查

### 查看服务状态
```bash
sudo systemctl status netconf-server
```

### 查看实时日志
```bash
# systemd 服务
sudo journalctl -u netconf-server -f

# 手动启动
tail -f server.log
```

### 端口占用检查
```bash
sudo lsof -i :8080
# 或
sudo netstat -tulnp | grep 8080
```

### 手动测试
```bash
cd /opt/netconf
source venv/bin/activate
python start_server.py
```

---

## 📞 默认认证信息

- **用户名**: `info`
- **密码**: `mecPassw0rd`

⚠️ **重要**: 生产环境请务必修改默认密码！
