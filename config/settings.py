"""
配置常量模块
包含所有配置项和常量
"""

# ===================== 服务器认证信息 =====================
SERVER_USERNAME = "info"
SERVER_PASSWORD = "mecPassw0rd"

# ===================== Hosts文件条目 =====================
HOSTS_ENTRIES = [
    '10.37.224.243 hisips.shx.hsip.gov.cn',
    '10.37.225.216 fms.shx.hsip.gov.cn',
    '10.37.231.230 cts-svc.shx.hsip.gov.cn',
    '10.37.227.210 zfzg.shx.hsip.gov.cn'
]

# ===================== 医保系统地址 =====================
MEDICAL_HOSTS = [
    "hisips.shx.hsip.gov.cn",
    "fms.shx.hsip.gov.cn",
    "cts-svc.shx.hsip.gov.cn"
]

# ===================== 默认网络配置 =====================
DEFAULT_DNS = "10.37.128.3"
DEFAULT_MASK = "255.255.255.0"
DEFAULT_MTU = 1300
MEDICAL_GATEWAY = "10.35.128.1"

# ===================== 向日葵安装路径 =====================
SUNFLOWER_PATHS = [
    r"C:\Program Files\Oray\SunLogin\SunloginClient\AweSun.exe",
    r"C:\Program Files (x86)\Oray\SunLogin\SunloginClient\AweSun.exe",
    r"C:\Program Files\Oray\SunLogin\SunloginClient.exe",
    r"C:\Program Files (x86)\Oray\SunLogin\SunloginClient.exe",
    r"C:\Program Files\Oray\SunLogin\AweSun.exe",
    r"C:\Program Files (x86)\Oray\SunLogin\AweSun.exe",
    r"D:\Program Files\Oray\SunLogin\SunloginClient.exe",
    r"D:\Program Files (x86)\Oray\SunLogin\SunloginClient.exe",
    r"D:\Program Files\Oray\SunLogin\AweSun.exe",
    r"D:\Program Files (x86)\Oray\SunLogin\AweSun.exe",
    r"C:\Program Files\Oray\SunLogin\SunloginClient\sunlogin.exe",
    r"C:\Program Files (x86)\Oray\SunLogin\SunloginClient\sunlogin.exe",
    r"D:\Program Files\Oray\SunLogin\SunloginClient\sunlogin.exe",
    r"D:\Program Files (x86)\Oray\SunLogin\SunloginClient\sunlogin.exe",
    r"C:\Users\%USERNAME%\AppData\Local\Oray\SunLogin\SunloginClient\AweSun.exe",
    r"C:\Users\%USERNAME%\AppData\Local\Oray\SunLogin\AweSun.exe",
]

SUNFLOWER_DOWNLOAD_URL = "https://down.oray.com/sunlogin/windows/SunloginClient_ng.exe"

# ===================== GUI配置 =====================
WINDOW_TITLE = "医保网络配置工具"
WINDOW_SIZE = "800x600"
WINDOW_BG_COLOR = "#F5F7FA"
