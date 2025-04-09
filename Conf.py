import subprocess
import re

# 这个函数用于打印系统中所有的网卡和IP地址
def print_interfaces_and_ips():
    try:
        # 使用ipconfig命令在Windows上获取所有网卡的IP地址信息
        output = subprocess.check_output(['ipconfig'], shell=True).decode('gbk', errors='replace')
        print("系统中的网卡和IP地址信息：")
        print(output)
        return output
    except Exception as e:
        print(f"获取网卡和IP地址时出错: {e}")
    return None

# 这个函数用于查找与指定IP地址模式相关的网卡名称，并返回匹配的IP地址
def find_interface_by_ip_pattern(output, ip_pattern):
    try:
        # 按行分割命令输出
        lines = output.split('\n')
        for i, line in enumerate(lines):
            # 查找包含“以太网适配器”的行
            if '以太网适配器' in line:
                # 提取以太网适配器名称
                interface_name = line.split('以太网适配器')[1].split(':')[0].strip()
                print(f"找到的网卡名称: {interface_name}")
                # 检查接下来的行是否有匹配的IP地址
                for j in range(i + 1, len(lines)):
                    ip_match = re.search(r'IPv4 地址 .+? (\d+\.\d+\.\d+\.\d+)', lines[j])
                    if ip_match:
                        ip_address = ip_match.group(1)
                        print(f"找到的IPv4地址: {ip_address}")
                        if re.match(ip_pattern, ip_address):
                            return interface_name, ip_address
        return None, None
    except Exception as e:
        print(f"查找网卡时出错: {e}")
    return None, None

# 这个函数用于修改指定网卡的MTU
def change_mtu(interface_name, mtu):
    try:
        # 使用netsh命令在Windows上修改网卡的MTU
        command = ['netsh', 'interface', 'ipv4', 'set', 'interface', interface_name, 'mtu={}'.format(mtu)]
        print(f"执行的命令: {' '.join(command)}")
        subprocess.run(command, check=True)
        print(f"网卡 {interface_name} 的MTU已成功修改为 {mtu}")
    except Exception as e:
        print(f"修改MTU时出错: {e}")

# 这个函数用于添加路由
def add_route(ip_address):
    try:
        # 提取IP地址的前三段
        network_segment = '.'.join(ip_address.split('.')[:-1])
        # 构建网关地址
        gateway = f"{network_segment}.1"
        # 使用route命令添加路由
        command = ['route', '-p', 'add', '10.0.0.0', 'mask', '255.0.0.0', gateway]
        print(f"执行的命令: {' '.join(command)}")
        subprocess.run(command, check=True)
        print(f"已成功添加路由至 10.0.0.0，网关为 {gateway}")
    except Exception as e:
        print(f"添加路由时出错: {e}")

# 打印系统中的所有网卡和IP地址
output = print_interfaces_and_ips()

# 指定要查找的IP地址模式
ip_pattern = r'10\.36\.[0-9]+\.[0-9]+'
# 查找对应的网卡名称和IP地址
interface_name, ip_address = find_interface_by_ip_pattern(output, ip_pattern)
if interface_name and ip_address:
    # 如果找到了网卡名称和IP地址，则修改其MTU并添加路由
    change_mtu(interface_name, 1300)
    add_route(ip_address)
else:
    print(f"未找到与IP地址模式 {ip_pattern} 相关的网卡")
