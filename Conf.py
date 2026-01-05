import subprocess
import re
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import webbrowser

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

# ===================== 获取网卡 + IPv4（原逻辑，未改） =====================
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

# ===================== 校验信息获取 =====================
def get_mtu_by_iface(iface):
    """
    使用：
    netsh interface ipv4 show interface <iface>
    正则匹配 MTU，最终返回 mtu=1300
    """
    output = subprocess.check_output(
        f'netsh interface ipv4 show interface "{iface}"',
        shell=True,
        encoding='gbk',
        errors='ignore'
    )

    match = re.search(r'MTU\s*:\s*(\d+)', output)
    if match:
        return f"mtu={match.group(1)}"
    return "mtu=未知"

def get_routes():
    return subprocess.check_output(
        'route print -4',
        shell=True,
        encoding='gbk',
        errors='ignore'
    )

# ===================== GUI =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("医保网络配置工具")
        self.root.geometry("720x560")
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

        tk.Label(
            self.root, text="医保网络配置工具",
            font=self.font_title, bg="#2F6FED", fg="white", pady=12
        ).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(
            card, text="请选择需要配置的网卡",
            font=("微软雅黑", 11, "bold"), bg="white"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.lb = tk.Listbox(card, width=85, height=8, font=self.font_normal)
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=15, pady=5)

        tk.Button(
            card, text="下一步",
            font=self.font_btn,
            bg="#2F6FED", fg="white",
            width=14,
            command=self.page_config
        ).pack(pady=15)

    # ---------- 页面 2 ----------
    def page_config(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择网卡")
            return

        self.iface = self.ifaces[sel[0]][0]
        self.clear()

        tk.Label(
            self.root, text="网络参数配置",
            font=self.font_title, bg="#2F6FED", fg="white", pady=12
        ).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(
            card, text=f"当前网卡：{self.iface}",
            bg="white", font=("微软雅黑", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.ip = self.add_entry(card, "IP 地址", "10.36.")
        self.mask = self.add_entry(card, "子网掩码", "255.255.255.0")
        self.dns = self.add_entry(card, "DNS", "10.37.128.3")

        tk.Button(
            card, text="开始配置",
            font=self.font_btn,
            bg="#16A34A", fg="white",
            width=16,
            command=self.apply
        ).pack(pady=20)

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
        try:
            ip = self.ip.get().strip()
            mask = self.mask.get().strip()
            dns = self.dns.get().strip()

            set_static_ip(self.iface, ip, mask)
            set_dns(self.iface, dns)

            gw = ".".join(ip.split(".")[:-1]) + ".1"
            add_route(gw)

            set_mtu(self.iface, 1300)
            modify_hosts()

            messagebox.showinfo("完成", "配置完成，进入校验页面")
            self.page_verify()

        except Exception as e:
            messagebox.showerror("失败", str(e))

    # ---------- 页面 3：校验 ----------
    def page_verify(self):
        self.clear()

        tk.Label(
            self.root, text="配置校验",
            font=self.font_title, bg="#2F6FED", fg="white", pady=12
        ).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 实时 IP
        current_ifaces = get_interfaces()
        ip = "未获取"
        for name, addr in current_ifaces:
            if name == self.iface:
                ip = addr
                break

        mtu = get_mtu_by_iface(self.iface)
        routes = get_routes()

        def row(k, v):
            f = tk.Frame(card, bg="white")
            f.pack(anchor="w", padx=15, pady=6, fill=tk.X)
            tk.Label(f, text=k, width=12, bg="white",
                     font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
            tk.Label(f, text=v, bg="white",
                     justify="left").pack(side=tk.LEFT)

        row("网卡名称", self.iface)
        row("IPv4 地址", ip)
        row("MTU", mtu)

        tk.Label(card, text="IPv4 路由表",
                 bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        txt = tk.Text(card, height=10, width=95, font=("Consolas", 9))
        txt.pack(padx=15)
        txt.insert(tk.END, routes)
        txt.config(state=tk.DISABLED)

        link = tk.Label(
            card,
            text="hisips.shx.hsip.gov.cn",
            fg="#2563EB",
            bg="white",
            cursor="hand2",
            font=("微软雅黑", 10, "underline")
        )
        link.pack(anchor="w", padx=15, pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open("http://hisips.shx.hsip.gov.cn"))

        tk.Button(
            card, text="关闭",
            font=self.font_btn,
            bg="#6B7280", fg="white",
            width=12,
            command=self.root.destroy
        ).pack(pady=15)

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
