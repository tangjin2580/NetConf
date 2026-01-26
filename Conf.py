import subprocess
import re
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import webbrowser
import os
import socket
import threading

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
        '10.37.231.230 cts-svc.shx.hsip.gov.cn',
        '10.37.227.210 zfzg.shx.hsip.gov.cn'
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

# ===================== 线程工具 =====================
def run_in_thread(func, on_done=None, on_error=None):
    def wrapper():
        try:
            result = func()
            if on_done:
                root.after(0, lambda: on_done(result))
        except Exception as e:
            if on_error:
                root.after(0, lambda: on_error(e))
    threading.Thread(target=wrapper, daemon=True).start()

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

        self.page_menu()

    # 创建按钮组件
    def create_button(self, parent, text, command, width=24, height=2, color="#2563EB"):
        tk.Button(parent, text=text, font=self.font_btn, bg=color, fg="white", width=width, height=height, command=command).pack(pady=15)

    # 创建标签组件
    def create_label(self, parent, text, font=("微软雅黑", 10, "bold"), pady=10):
        tk.Label(parent, text=text, font=font, bg="white").pack(anchor="w", padx=15, pady=pady)

    # ---------- 一级菜单 ----------
    def page_menu(self):
        self.clear()
        tk.Label(self.root, text="医保网络配置工具", font=self.font_title, bg="#2F6FED", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

        tk.Label(card, text="请选择功能", font=("微软雅黑", 13, "bold"), bg="white").pack(pady=30)

        self.create_button(card, "🧾 仅补全 hosts 文件", self.page_hosts_only, color="#16A34A")
        self.create_button(card, "🌐 IP / MTU / 路由配置", self.page_select, color="#2563EB")

    # ---------- hosts 补全页面 ----------
    def page_hosts_only(self):
        self.clear()
        tk.Label(self.root, text="hosts 文件补全", font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        status = tk.Label(card, text="等待操作", bg="white", font=("微软雅黑", 10))
        status.pack(pady=40)

        def do_hosts():
            if hosts_already_set():
                return "hosts 已存在，无需修改"
            modify_hosts()
            return "hosts 补全完成"

        def on_done(msg):
            status.config(text=msg)
            messagebox.showinfo("完成", msg)

        self.create_button(card, "开始补全 hosts", lambda: run_in_thread(do_hosts, on_done), width=20, color="#16A34A")
        self.create_button(card, "返回", self.page_menu, width=12, color="#6B7280")

    # ---------- 网卡选择页面 ----------
    def page_select(self):
        self.clear()
        tk.Label(self.root, text="医保网络配置工具", font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(card, text="请选择需要配置的网卡", font=("微软雅黑", 11, "bold"), bg="white").pack(anchor="w", padx=15, pady=(15, 5))

        self.lb = tk.Listbox(card, width=95, height=8, font=self.font_normal)
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=15, pady=5)

        self.create_button(card, "下一步", self.page_config, width=14, color="#2F6FED")

    # ---------- 配置页面 ----------
    def page_config(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择网卡")
            return

        self.iface = self.ifaces[sel[0]][0]
        self.clear()

        tk.Label(self.root, text="网络参数配置", font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(card, text=f"当前网卡：{self.iface}", bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        self.ip = self.add_entry(card, "IP 地址", "10.36.")
        self.mask = self.add_entry(card, "子网掩码", "255.255.255.0")
        self.dns = self.add_entry(card, "DNS", "10.37.128.3")

        f_btn = tk.Frame(card, bg="white")
        f_btn.pack(pady=20)
        self.create_button(f_btn, "开始配置", self.apply, width=16, color="#16A34A")
        self.create_button(f_btn, "强制重新配置", self.force_apply, width=16, color="#F59E0B")

    def add_entry(self, parent, label, default):
        f = tk.Frame(parent, bg="white")
        f.pack(anchor="w", padx=15, pady=5)
        tk.Label(f, text=label, width=10, bg="white").pack(side=tk.LEFT)
        e = tk.Entry(f, width=32)
        e.pack(side=tk.LEFT)
        e.insert(0, default)
        return e

    # ---------- 提交配置 ----------
    def apply(self):
        self._apply_async(force=False)

    def force_apply(self):
        self._apply_async(force=True)

    def _apply_async(self, force=False):
        ip = self.ip.get().strip()
        mask = self.mask.get().strip()
        dns = self.dns.get().strip()

        def task():
            missing = get_missing_items(self.iface)
            if force:
                missing = ["IP 地址", "MTU", "hosts 文件"]
            if missing:
                apply_missing_config(self.iface, ip, mask, dns, missing)
            return missing

        def on_done(missing):
            if not missing and not force:
                messagebox.showinfo("无需配置", "配置已存在，进入校验页面")
            else:
                messagebox.showinfo("完成", "配置完成，进入校验页面")
            self.page_verify()

        def on_error(e):
            messagebox.showerror("失败", str(e))

        run_in_thread(task, on_done, on_error)

    # ---------- 校验页面 ----------
    def page_verify(self):
        self.clear()
        tk.Label(self.root, text="配置校验", font=self.font_title, bg="#2F6FED", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        ip = "未获取"
        for name, addr in get_interfaces():
            if name == self.iface:
                ip = addr
                break

        def row_status(title, ok):
            f = tk.Frame(card, bg="white")
            f.pack(anchor="w", padx=15, pady=6)
            tk.Label(f, text=title, width=12, bg="white", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
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

        tk.Label(card, text="IPv4 路由表", bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        txt = tk.Text(card, height=10, width=95, font=("Consolas", 9))
        txt.pack(padx=15)
        txt.insert(tk.END, get_routes())
        txt.config(state=tk.DISABLED)

        tk.Label(card, text="医保地址连通性测试", bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        hosts = ["hisips.shx.hsip.gov.cn", "fms.shx.hsip.gov.cn", "cts-svc.shx.hsip.gov.cn"]
        for h in hosts:
            ok = test_host_connectivity(h)
            lbl = tk.Label(card, text=f"{h}: {'🟢 可访问' if ok else '🔴 不可访问'}", bg="white", font=("微软雅黑", 10))
            lbl.pack(anchor="w", padx=25)

        link = tk.Label(card, text="访问医保官网", fg="#2563EB", bg="white", cursor="hand2", font=("微软雅黑", 10, "underline"))
        link.pack(anchor="w", padx=15, pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open("http://hisips.shx.hsip.gov.cn"))

        self.create_button(card, "关闭", self.root.destroy, width=12, color="#6B7280")

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
