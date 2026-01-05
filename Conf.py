import subprocess
import re
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import webbrowser
import os
import socket

# ===================== 管理员权限检测 =====================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("权限不足", "请右键以【管理员身份】运行本程序")
    sys.exit(1)

# ===================== 获取网卡 + IPv4 =====================
def get_interfaces():
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

# ===================== 系统命令 =====================
def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

def set_static_ip(iface, ip, mask):
    run(f'netsh interface ipv4 set address name="{iface}" static {ip} {mask}')

def set_dns(iface, dns):
    run(f'netsh interface ipv4 set dns name="{iface}" static {dns}')

def set_mtu(iface, mtu):
    run(f'netsh interface ipv4 set subinterface "{iface}" mtu={mtu} store=persistent')

def add_route(gateway):
    run(f'route -p add 10.0.0.0 mask 255.0.0.0 {gateway}')

def modify_hosts():
    hosts = r'C:\Windows\System32\drivers\etc\hosts'
    entries = [
        '10.37.224.243 hisips.shx.hsip.gov.cn',
        '10.37.225.216 fms.shx.hsip.gov.cn',
        '10.37.231.230 cts-svc.shx.hsip.gov.cn'
    ]
    with open(hosts, 'a', encoding='utf-8') as f:
        f.write('\n# 医保系统\n')
        for e in entries:
            f.write(e + '\n')

# ===================== 校验函数 =====================
def ip_already_set(iface):
    for name, ip in get_interfaces():
        if name == iface and ip.startswith("10.36."):
            return True
    return False

def mtu_already_set(iface):
    output = subprocess.check_output(
        f'netsh interface ipv4 show interface "{iface}"',
        shell=True,
        encoding='gbk',
        errors='ignore'
    )
    return bool(re.search(r'MTU\s*:\s*1300', output))

def hosts_already_set():
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

def get_missing_items(iface):
    missing = []
    if not ip_already_set(iface):
        missing.append("IP 地址")
    if not mtu_already_set(iface):
        missing.append("MTU")
    if not hosts_already_set():
        missing.append("hosts 文件")
    return missing

def apply_missing_config(iface, ip, mask, dns, missing):
    if "IP 地址" in missing:
        set_static_ip(iface, ip, mask)
        set_dns(iface, dns)
        add_route(".".join(ip.split(".")[:-1]) + ".1")
    if "MTU" in missing:
        set_mtu(iface, 1300)
    if "hosts 文件" in missing:
        modify_hosts()

def get_mtu_by_iface(iface):
    output = subprocess.check_output(
        f'netsh interface ipv4 show interface "{iface}"',
        shell=True,
        encoding='gbk',
        errors='ignore'
    )
    match = re.search(r'MTU\s*:\s*(\d+)', output)
    return f"mtu={match.group(1)}" if match else "mtu=未知"

def get_routes():
    return subprocess.check_output(
        'route print -4',
        shell=True,
        encoding='gbk',
        errors='ignore'
    )

def test_host_connectivity(host, port=80, timeout=3):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except:
        return False

# ===================== GUI =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("医保网络配置工具")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#F5F7FA")

        self.font_title = ("微软雅黑", 16, "bold")
        self.font_normal = ("微软雅黑", 10)
        self.font_btn = ("微软雅黑", 10, "bold")

        self.ifaces = get_interfaces()
        if not self.ifaces:
            messagebox.showerror("错误", "未获取到任何网卡")
            root.destroy()
            return

        self.page_select()

    # ---------- 页面 1 ----------
    def page_select(self):
        self.clear()
        tk.Label(self.root, text="医保网络配置工具",
                 font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(card, text="请选择需要配置的网卡",
                 font=("微软雅黑", 11, "bold"), bg="white").pack(anchor="w", padx=15, pady=(15, 5))

        self.lb = tk.Listbox(card, width=95, height=8, font=self.font_normal)
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=15, pady=5)

        tk.Button(card, text="下一步", font=self.font_btn,
                  bg="#2F6FED", fg="white", width=14,
                  command=self.page_config).pack(pady=15)

    # ---------- 页面 2 ----------
    def page_config(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择网卡")
            return

        self.iface = self.ifaces[sel[0]][0]
        self.clear()

        tk.Label(self.root, text="网络参数配置",
                 font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(card, text=f"当前网卡：{self.iface}",
                 bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        self.ip = self.add_entry(card, "IP 地址", "10.36.")
        self.mask = self.add_entry(card, "子网掩码", "255.255.255.0")
        self.dns = self.add_entry(card, "DNS", "10.37.128.3")

        f_btn = tk.Frame(card, bg="white")
        f_btn.pack(pady=20)
        tk.Button(f_btn, text="开始配置", font=self.font_btn,
                  bg="#16A34A", fg="white", width=16,
                  command=self.apply).pack(side=tk.LEFT, padx=10)
        tk.Button(f_btn, text="强制重新配置", font=self.font_btn,
                  bg="#F59E0B", fg="white", width=16,
                  command=self.force_apply).pack(side=tk.LEFT, padx=10)

    def add_entry(self, parent, label, default):
        f = tk.Frame(parent, bg="white")
        f.pack(anchor="w", padx=15, pady=5)
        tk.Label(f, text=label, width=10, bg="white").pack(side=tk.LEFT)
        e = tk.Entry(f, width=32)
        e.pack(side=tk.LEFT)
        e.insert(0, default)
        return e

    # ---------- 应用配置 ----------
    def apply(self):
        self._apply(force=False)

    def force_apply(self):
        self._apply(force=True)

    def _apply(self, force=False):
        try:
            ip = self.ip.get().strip()
            mask = self.mask.get().strip()
            dns = self.dns.get().strip()

            missing = get_missing_items(self.iface)
            if force:
                # 全部强制补齐
                missing = ["IP 地址", "MTU", "hosts 文件"]

            if not missing and not force:
                messagebox.showinfo(
                    "无需配置",
                    "检测到 IP、MTU、hosts 均已配置完成，直接进入校验页面"
                )
                self.page_verify()
                return

            if missing:
                messagebox.showinfo(
                    "检测到配置缺失",
                    "将自动补齐以下配置：\n\n" + "\n".join(missing)
                )
                apply_missing_config(self.iface, ip, mask, dns, missing)

            messagebox.showinfo("完成", "缺失配置已补齐，进入校验页面")
            self.page_verify()

        except Exception as e:
            messagebox.showerror("失败", str(e))

    # ---------- 校验页面 ----------
    def page_verify(self):
        self.clear()
        tk.Label(self.root, text="配置校验",
                 font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 实时 IP
        ip = "未获取"
        for name, addr in get_interfaces():
            if name == self.iface:
                ip = addr
                break

        # 校验项显示
        def row_status(title, ok):
            f = tk.Frame(card, bg="white")
            f.pack(anchor="w", padx=15, pady=6)
            tk.Label(f, text=title, width=12, bg="white",
                     font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
            status = "🟢 已配置" if ok else "🔴 缺失"
            lbl = tk.Label(f, text=status, bg="white", font=("微软雅黑", 10))
            lbl.pack(side=tk.LEFT)
            return lbl

        ip_ok = ip_already_set(self.iface)
        mtu_ok = mtu_already_set(self.iface)
        hosts_ok = hosts_already_set()
        ip_row = row_status("IP 地址", ip_ok)
        mtu_row = row_status("MTU", mtu_ok)
        hosts_row = row_status("hosts 文件", hosts_ok)

        # 路由表
        tk.Label(card, text="IPv4 路由表",
                 bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        txt = tk.Text(card, height=10, width=95, font=("Consolas", 9))
        txt.pack(padx=15)
        txt.insert(tk.END, get_routes())
        txt.config(state=tk.DISABLED)

        # 访问测试
        tk.Label(card, text="医保地址连通性测试",
                 bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        hosts = ["hisips.shx.hsip.gov.cn", "fms.shx.hsip.gov.cn", "cts-svc.shx.hsip.gov.cn"]
        for h in hosts:
            ok = test_host_connectivity(h)
            lbl = tk.Label(card, text=f"{h}: {'🟢 可访问' if ok else '🔴 不可访问'}",
                           bg="white", font=("微软雅黑", 10))
            lbl.pack(anchor="w", padx=25)

        # 医保官网链接
        link = tk.Label(card, text="访问医保官网", fg="#2563EB", bg="white", cursor="hand2",
                        font=("微软雅黑", 10, "underline"))
        link.pack(anchor="w", padx=15, pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open("http://hisips.shx.hsip.gov.cn"))

        tk.Button(card, text="关闭", font=self.font_btn,
                  bg="#6B7280", fg="white", width=12,
                  command=self.root.destroy).pack(pady=15)

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
