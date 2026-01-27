"""
Hosts文件管理模块
包含Hosts文件的读取、修改、检查等功能
"""
import os
from config.settings import HOSTS_ENTRIES


def modify_hosts():
    """修改hosts文件，添加医保系统条目"""
    hosts = r'C:\Windows\System32\drivers\etc\hosts'
    added_entries = []
    
    with open(hosts, 'r', encoding='utf-8', errors='ignore') as f:
        existing_content = f.read()

    # 检查哪些条目需要添加
    with open(hosts, 'a', encoding='utf-8') as f:
        f.write('\n# 医保系统\n')
        for entry in HOSTS_ENTRIES:
            if entry.split()[1] not in existing_content:
                f.write(entry + '\n')
                added_entries.append(entry)

    return added_entries


def check_hosts_status():
    """检查hosts文件状态，返回完整性和缺失条目"""
    hosts = r'C:\Windows\System32\drivers\etc\hosts'
    
    if not os.path.exists(hosts):
        return False, HOSTS_ENTRIES, []
    
    with open(hosts, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    existing = []
    missing = []
    for entry in HOSTS_ENTRIES:
        ip, domain = entry.split()
        if domain in content:
            existing.append(entry)
        else:
            missing.append(entry)
    
    is_complete = len(missing) == 0
    return is_complete, missing, existing


def hosts_already_set():
    """判断hosts文件是否已经配置"""
    hosts = r'C:\Windows\System32\drivers\etc\hosts'
    if not os.path.exists(hosts):
        return False

    with open(hosts, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    return (
        'hisips.shx.hsip.gov.cn' in content or
        'fms.shx.hsip.gov.cn' in content or
        'cts-svc.shx.hsip.gov.cn' in content
    )
