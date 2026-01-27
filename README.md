# 医保网络配置工具

针对 Windows 7 - Windows 11 的医保网络配置工具，支持静态IP、路由、MTU和hosts文件配置。

## 功能特性

### 1. 双WAN配置（路由器）
- **自动获取路由器IP**：从路由表自动检测默认网关（0.0.0.0 mask 0.0.0.0）
- **向日葵远程控制**：检测与启动远程协助
- **一键设置MTU**：自动将所有网卡MTU设置为1300（无需勾选）
- **信息管理服务器**：内置HTTP服务器，支持：
  - 文件管理（上传、下载、删除）
  - 在线编辑txt/md文件
  - 下载协议支持

### 2. 单机配置（直连）
- hosts文件智能补全（检查缺失条目）
- 单网卡IP/MTU/路由配置
- 配置状态校验
- 医保地址连通性测试

## 使用方法

### 1. 运行程序
```bash
# 使用Python直接运行
python Conf.py

# 或双击Conf.py运行
```

### 2. 双WAN配置
- 程序会自动从路由表获取路由器IP
- 如未检测到，可手动输入
- 点击"开始双WAN配置"一键设置所有网卡MTU=1300

### 3. 信息管理服务器
在双WAN配置页面右侧：
1. 点击"启动服务器"按钮
2. 浏览器访问：`http://localhost:8080`
3. 支持功能：
   - 查看文件列表
   - 上传新文件
   - 在线编辑文本文件
   - 下载文件

## API接口

### 列出文件
```
GET /api/files
```
返回所有文件列表（JSON格式）

### 上传文件
```
POST /api/upload
Content-Type: multipart/form-data

file: <文件内容>
```

### 保存文件
```
POST /api/save
Content-Type: application/json

{
  "filename": "文件名.txt",
  "content": "文件内容"
}
```

### 下载文件
```
GET /download/文件名.txt
```

## 项目结构

```
NetConf/
├── Conf.py              # 主程序文件
├── Conf.spec            # PyInstaller配置文件
├── icon.ico             # 程序图标
├── requirements.txt     # Python依赖
├── README.md           # 本说明文件
├── info/               # 信息展示文件夹（服务器根目录）
│   └── 双WAN配置说明.txt  # 示例文件
├── .git/               # Git版本控制
├── .github/            # GitHub配置
└── .idea/              # PyCharm IDE配置
```

## 系统要求
- Windows 7 / 8 / 10 / 11
- Python 3.7+
- 需要管理员权限运行

## 依赖安装
```bash
pip install -r requirements.txt
```

## 注意事项
1. **必须以管理员身份运行**（右键 → 以管理员身份运行）
2. 修改网络配置前建议备份当前设置
3. MTU修改后可能需要重启网卡生效
4. 信息服务器默认端口：8080

## 作者
tangjin
