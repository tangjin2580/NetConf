"""
系统检查模块
包含管理员权限检查、向日葵检测、配置检查等功能
"""
import ctypes
import os
import webbrowser
from config.settings import SUNFLOWER_PATHS, SUNFLOWER_DOWNLOAD_URL
from core.network import ip_already_set, mtu_already_set, route_already_set, set_static_ip, set_dns, add_route, set_mtu
from core.hosts import hosts_already_set, modify_hosts


def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def check_sunflower_installed():
    """检查向日葵是否已安装 - 优化的检测逻辑"""
    for path in SUNFLOWER_PATHS:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            return True, expanded_path
    
    # 如果都没找到，尝试从注册表获取
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\SunloginClient")
        install_location = winreg.QueryValueEx(key, "InstallLocation")[0]
        exe_path = os.path.join(install_location, "AweSun.exe")
        if os.path.exists(exe_path):
            return True, exe_path
        winreg.CloseKey(key)
    except:
        pass
    
    return False, None


def download_sunflower():
    """下载向日葵远程"""
    try:
        webbrowser.open(SUNFLOWER_DOWNLOAD_URL)
        return True
    except:
        return False


def get_missing_items(iface):
    """获取缺失的配置项"""
    missing = []
    if not ip_already_set(iface):
        missing.append("IP 地址")
    if not mtu_already_set(iface):
        missing.append("MTU")
    if not hosts_already_set():
        missing.append("hosts 文件")
    if not route_already_set():
        missing.append("路由")
    return missing


def apply_missing_config(iface, ip, mask, dns, missing, progress_callback=None):
    """应用缺失的配置，支持进度回调"""
    total = len(missing)
    current = 0
    
    if "IP 地址" in missing:
        set_static_ip(iface, ip, mask)
        set_dns(iface, dns)
        current += 1
        if progress_callback:
            progress_callback(current, total, "正在配置IP地址...")
    
    if "路由" in missing:
        gateway = ".".join(ip.split(".")[:-1]) + ".1"
        add_route(gateway)
        current += 1
        if progress_callback:
            progress_callback(current, total, "正在添加路由...")
    
    if "MTU" in missing:
        set_mtu(iface, 1300)
        current += 1
        if progress_callback:
            progress_callback(current, total, "正在设置MTU...")
    
    if "hosts 文件" in missing:
        modify_hosts()
        current += 1
        if progress_callback:
            progress_callback(current, total, "正在修改hosts文件...")
