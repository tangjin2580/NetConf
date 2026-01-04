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


# ===================== GUI =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("医保网络配置工具")
        self.root.geometry("600x420")
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

        # 标题
        tk.Label(
            self.root, text="医保网络配置工具",
            font=self.font_title, bg="#2F6FED", fg="white",
            pady=12
        ).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white", bd=1, relief=tk.FLAT)
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(
            card, text="请选择需要配置的网卡",
            font=("微软雅黑", 11, "bold"), bg="white"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.lb = tk.Listbox(
            card, width=70, height=8,
            font=self.font_normal, bd=1, relief=tk.SOLID
        )
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=15, pady=5)

        tk.Button(
            card, text="下一步",
            font=self.font_btn,
            bg="#2F6FED", fg="white",
            activebackground="#1E4ED8",
            width=14, height=1,
            command=self.page_config
        ).pack(pady=15)

        tk.Label(
            self.root,
            text="提示：请确认当前电脑已连接医保专网",
            bg="#F5F7FA", fg="#666", font=("微软雅黑", 9)
        ).pack(pady=(0, 10))

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
            font=self.font_title, bg="#2F6FED", fg="white",
            pady=12
        ).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(
            card, text=f"当前网卡：{self.iface}",
            bg="white", fg="#333", font=("微软雅黑", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.ip = self.add_entry(card, "IP 地址", "10.36.")
        self.mask = self.add_entry(card, "子网掩码", "255.255.255.0")
        self.dns = self.add_entry(card, "DNS", "10.37.128.3")

        tk.Button(
            card, text="开始配置",
            font=self.font_btn,
            bg="#16A34A", fg="white",
            activebackground="#15803D",
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

            messagebox.showinfo("完成", "配置完成，请重新插拔网线")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
