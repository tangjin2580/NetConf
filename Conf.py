import subprocess
import re
import tkinter as tk
from tkinter import messagebox

# ===================== 获取网卡 & IP =====================
def get_interfaces():
    output = subprocess.check_output("ipconfig", shell=True, encoding="gbk", errors="ignore")

    blocks = re.split(r"\r?\n\r?\n", output)
    interfaces = []

    for block in blocks:
        name_match = re.search(r"适配器\s+(.+?):", block)
        if not name_match:
            continue

        name = name_match.group(1).strip()

        ip_match = re.search(
            r"\b(?!169\.254)(\d{1,3}(?:\.\d{1,3}){3})\b",
            block
        )

        ip = ip_match.group(1) if ip_match else "未获取"

        interfaces.append((name, ip))

    return interfaces


# ===================== 网络操作 =====================
def set_static_ip(iface, ip, mask):
    subprocess.run(
        f'netsh interface ipv4 set address "{iface}" static {ip} {mask}',
        shell=True,
        check=True
    )


def set_dns(iface, dns):
    subprocess.run(
        f'netsh interface ipv4 set dns "{iface}" static {dns} primary',
        shell=True,
        check=True
    )


def set_mtu(iface, mtu):
    subprocess.run(
        f'netsh interface ipv4 set subinterface "{iface}" mtu={mtu} store=persistent',
        shell=True,
        check=True
    )


def add_route(gateway):
    subprocess.run(
        f'route -p add 10.0.0.0 mask 255.0.0.0 {gateway}',
        shell=True,
        check=True
    )


def modify_hosts():
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    entries = [
        "10.37.224.243 hisips.shx.hsip.gov.cn",
        "10.37.225.216 fms.shx.hsip.gov.cn",
        "10.37.231.230 cts-svc.shx.hsip.gov.cn",
    ]

    with open(hosts_path, "a", encoding="utf-8") as f:
        f.write("\n# 医保系统\n")
        for e in entries:
            f.write(e + "\n")


# ===================== GUI =====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("网络配置工具")

        self.ifaces = get_interfaces()
        if not self.ifaces:
            messagebox.showerror("错误", "未获取到任何网卡")
            root.destroy()
            return

        self.page1()

    def page1(self):
        self.clear()

        tk.Label(self.root, text="选择网卡", font=("微软雅黑", 12)).pack(pady=5)

        self.lb = tk.Listbox(self.root, width=50, height=8)
        for n, ip in self.ifaces:
            self.lb.insert(tk.END, f"{n}    [{ip}]")
        self.lb.pack()

        tk.Button(self.root, text="下一步", command=self.page2).pack(pady=10)

    def page2(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择网卡")
            return

        self.iface = self.ifaces[sel[0]][0]

        self.clear()

        tk.Label(self.root, text=f"网卡：{self.iface}", fg="blue").pack(pady=5)

        self.ip = self.entry("IP 地址")
        self.mask = self.entry("子网掩码", "255.255.255.0")
        self.dns = self.entry("DNS", "114.114.114.114")

        tk.Button(self.root, text="开始配置", command=self.apply).pack(pady=10)

    def apply(self):
        try:
            set_static_ip(self.iface, self.ip.get(), self.mask.get())
            set_dns(self.iface, self.dns.get())

            gw = ".".join(self.ip.get().split(".")[:-1]) + ".1"
            add_route(gw)

            set_mtu(self.iface, 1300)
            modify_hosts()

            messagebox.showinfo("完成", "配置完成，请重新插拔网线")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def entry(self, label, default=""):
        frame = tk.Frame(self.root)
        frame.pack(pady=3)
        tk.Label(frame, text=label, width=10).pack(side=tk.LEFT)
        e = tk.Entry(frame, width=30)
        e.pack(side=tk.LEFT)
        e.insert(0, default)
        return e

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
