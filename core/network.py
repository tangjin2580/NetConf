"""
网络工具模块
包含所有网络相关的操作函数
"""
import subprocess
import re
import socket


def get_interfaces():
    """获取所有网卡及其IP地址"""
    output = subprocess.check_output(
        "ipconfig /all",
        shell=True,
        encoding="gbk",
        errors="ignore"
    )

    interfaces = []
    current_iface = None
    current_ip = None

    for line in output.splitlines():
        line = line.strip()

        name_match = re.match(
            r'(以太网适配器|无线局域网适配器|Ethernet adapter|Wireless LAN adapter)\s+(.+?):',
            line
        )
        if name_match:
            if current_iface:
                interfaces.append((current_iface, current_ip or "未获取"))
            current_iface = name_match.group(2)
            current_ip = None
            continue

        if current_iface:
            ip_match = re.search(
                r'(IPv4 地址|IPv4 Address|IP Address)[^0-9]*(\d+\.\d+\.\d+\.\d+)',
                line
            )
            if ip_match:
                current_ip = ip_match.group(2)

    if current_iface:
        interfaces.append((current_iface, current_ip or "未获取"))

    return interfaces


def run(cmd):
    """执行系统命令"""
    subprocess.run(cmd, shell=True, check=True)


def set_static_ip(iface, ip, mask):
    """设置静态IP地址"""
    run(f'netsh interface ipv4 set address name="{iface}" static {ip} {mask}')


def set_dns(iface, dns):
    """设置DNS服务器"""
    run(f'netsh interface ipv4 set dns name="{iface}" static {dns}')


def set_mtu(iface, mtu):
    """设置MTU值"""
    run(f'netsh interface ipv4 set subinterface "{iface}" mtu={mtu} store=persistent')


def add_route(gateway):
    """添加永久路由"""
    run(f'route -p add 10.0.0.0 mask 255.0.0.0 {gateway}')


def set_all_mtu(mtu=1300):
    """设置所有网卡的MTU"""
    interfaces = get_interfaces()
    results = []
    for name, ip in interfaces:
        try:
            set_mtu(name, mtu)
            results.append(f"✓ {name} MTU已设置为 {mtu}")
        except Exception as e:
            results.append(f"✗ {name} 设置失败: {str(e)}")
    return results


def get_default_gateway():
    """从路由表中获取默认网关IP（0.0.0.0 mask 0.0.0.0）"""
    try:
        output = subprocess.check_output(
            'route print -4',
            shell=True,
            encoding='gbk',
            errors='ignore'
        )
        
        # 查找默认路由（0.0.0.0 mask 0.0.0.0）
        for line in output.splitlines():
            line = line.strip()
            if '0.0.0.0' in line and '0.0.0.0' in line:
                parts = line.split()
                if len(parts) >= 3:
                    for i, part in enumerate(parts):
                        if part == '0.0.0.0' and i > 0:
                            if i + 1 < len(parts) and parts[i + 1] == '0.0.0.0':
                                gateway = parts[i + 2] if i + 2 < len(parts) else None
                                if gateway and gateway != 'On-link':
                                    return gateway
        return None
    except:
        return None


def ping_host(host, count=4):
    """ping指定主机，返回是否成功和结果信息"""
    try:
        # Windows系统使用 -n 参数
        output = subprocess.check_output(
            f"ping -n {count} {host}",
            shell=True,
            encoding="gbk",
            errors="ignore",
            timeout=10
        )
        # 检查是否有成功的响应
        if "TTL=" in output or "ms" in output:
            # 提取统计信息
            if "已发送 = " in output:
                # 中文版本
                match = re.search(r'已发送 = (\d+)，已接收 = (\d+)，丢失 = (\d+)', output)
                if match:
                    sent, received, lost = match.groups()
                    return True, f"已发送 {sent} 个，已接收 {received} 个，丢失 {lost} 个"
            elif "Sent = " in output:
                # 英文版本
                match = re.search(r'Sent = (\d+), Received = (\d+), Lost = (\d+)', output)
                if match:
                    sent, received, lost = match.groups()
                    return True, f"Sent {sent}, Received {received}, Lost {lost}"
            return True, "ping 成功"
        return False, "ping 失败，无响应"
    except subprocess.TimeoutExpired:
        return False, "ping 超时"
    except Exception as e:
        return False, f"ping 失败: {str(e)}"


def test_host_connectivity(host, port=80, timeout=3):
    """测试主机端口连通性"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except:
        return False


def route_already_set():
    """检查路由是否已配置"""
    try:
        output = subprocess.check_output(
            'route print 10.0.0.0',
            shell=True,
            encoding='gbk',
            errors='ignore'
        )
        return '10.0.0.0' in output
    except:
        return False


def ip_already_set(iface):
    """检查指定网卡的IP是否已配置为10.36.x.x"""
    for name, ip in get_interfaces():
        if name == iface and ip.startswith("10.36."):
            return True
    return False


def mtu_already_set(iface):
    """检查指定网卡的MTU是否已设置为1300"""
    try:
        output = subprocess.check_output(
            f'netsh interface ipv4 show interface "{iface}"',
            shell=True,
            encoding='gbk',
            errors='ignore'
        )
        return bool(re.search(r'MTU\s*:\s*1300', output))
    except:
        return False
