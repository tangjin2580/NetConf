import subprocess
import re
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys

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

# ===================== 获取网卡 + IPv4（Win7–Win11） =====================
def get_interfaces():
    try:
        output = subprocess.check_output(
            "ipconfig /all",
            shell=True,
            encoding="gbk",
            errors="ignore"
        )
    except Exception as e:
        messagebox.showerror("错误", f"无法执行 ipconfig\n{e}")
        return []

    interfaces = []
    current_iface = None
    current_ip = None

    for line in output.splitlines():
        line = line.strip()

        # ---- 网卡名称（中英文，Win7-11）----
        name_match = re.match(
            r'(以太网适配器|无线局域网适配器|Ethernet adapter|Wireless LAN adapter)\s+(.+?):',
            line
        )
        if name_match:
            if current_iface:
                interfaces.append(
                    (current_iface, current_ip or "未获取")
                )
            current_iface = name_match.group(2)
            current_ip = None
            continue

        # ---- IPv4 地址 ----
        if current_iface:
            ip_match = re.search(
                r'(IPv4 地址|IPv4 Address|IP Address)[^0-9]*(\d+\.\d+\.\d+\.\d+)',
                line
            )
            if ip_match:
                current_ip = ip_match.group(2)

    # 最后一个网卡
    if current_iface:
        interfaces.append((current_iface, current_ip or "未获取"))

    return interfaces


# ===================== 系统命令封装 =====================
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
    hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    entries = [
        '10.37.224.243 hisips.shx.hsip.gov.cn',
        '10.37.225.216 fms.shx.hsip.gov.cn',
        '10.37.231.230 cts-svc.shx.hsip.gov.cn'
    ]

    with open(hosts_path, 'a', encoding='utf-8') as f:
        f.write('\n# 医保系统\n')
        for e in entries:
            f.write(e + '\n')


# ===================== GUI =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("医保网络配置工具")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        self.ifaces = get_interfaces()
        if not self.ifaces:
            messagebox.showerror("错误", "未获取到任何网卡\n请确认以管理员运行")
            root.destroy()
            return

        self.page_select_iface()

    # ---------- 页面 1：选择网卡 ----------
    def page_select_iface(self):
        self.clear()

        tk.Label(self.root, text="请选择网卡", font=("微软雅黑", 12)).pack(pady=10)

        self.lb = tk.Listbox(self.root, width=70, height=8)
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=10)

        tk.Button(self.root, text="下一步", width=15, command=self.page_config).pack(pady=10)

    # ---------- 页面 2：填写参数 ----------
    def page_config(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择一个网卡")
            return

        self.iface = self.ifaces[sel[0]][0]
        self.clear()

        tk.Label(self.root, text=f"当前网卡：{self.iface}", fg="blue").pack(pady=5)

        self.ip_entry = self.add_entry("IP 地址", "10.36.")
        self.mask_entry = self.add_entry("子网掩码", "255.255.255.0")
        self.dns_entry = self.add_entry("DNS", "10.37.128.3")

        tk.Button(self.root, text="开始配置", width=15, command=self.apply).pack(pady=15)

    # ---------- 执行配置 ----------
    def apply(self):
        try:
            ip = self.ip_entry.get().strip()
            mask = self.mask_entry.get().strip()
            dns = self.dns_entry.get().strip()

            set_static_ip(self.iface, ip, mask)
            set_dns(self.iface, dns)

            gateway = ".".join(ip.split(".")[:-1]) + ".1"
            add_route(gateway)

            set_mtu(self.iface, 1300)
            modify_hosts()

            messagebox.showinfo("完成", "配置完成，请重新插拔网线")
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("失败", str(e))

    # ---------- UI 工具 ----------
    def add_entry(self, label, default):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Label(frame, text=label, width=10).pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=30)
        entry.pack(side=tk.LEFT)
        entry.insert(0, default)
        return entry

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
