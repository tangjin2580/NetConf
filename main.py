import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import webbrowser
import os
import threading
from datetime import datetime
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None
try:
    import requests
except Exception:
    requests = None
import re
import json
import time

# 导入配置（包含版本信息）
from config import *
from core.network import *
from core.hosts import *
from core.system import *
from utils.cache import *
# 可选加载服务器模块，避免依赖缺失导致界面无法启动
SERVER_AVAILABLE = True
try:
    from utils.server import *
except Exception:
    SERVER_AVAILABLE = False
    def check_server_status(server_url):
        return False, None
    def fetch_server_files(server_url):
        return []
    def download_file_to_cache(server_url, filename):
        return None
    def fetch_file_content(server_url, filename):
        return None

# ===================== 版本检查工具 =====================
import os
from config.settings import LOCAL_VERSION, GITHUB_API_URL, GITHUB_RELEASES_URL, FASTGIT_RELEASES_URL, PROXY_RELEASES_URLS

def log_error(message):
    try:
        cache_dir = get_cache_folder()
        path = os.path.join(cache_dir, "startup.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass

def check_for_updates():
    """检查是否有新版本可用"""
    try:
        # 使用从settings.py中获取的本地版本
        local_version = LOCAL_VERSION
        if not local_version:
            print("无法读取本地版本号")
            return None, None, None, None

        # 请求 GitHub 获取最新版本
        if not requests:
            return None, None, None, None
        response = requests.get(GITHUB_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')
            if latest_version:
                # 比较版本号
                if is_update_available(local_version, latest_version):
                    return latest_version, data.get('html_url', ''), data.get('published_at', ''), data.get('body', '')
    except Exception as e:
        print(f"检查更新失败: {e}")
    return None, None, None, None

def parse_version(version_str):
    """解析版本号为可比较的元组"""
    try:
        nums = re.findall(r'\d+', version_str)
        parts = [int(n) for n in nums[:3]]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except:
        return (0, 0, 0)

def is_update_available(current_version, latest_version):
    """检查是否有新版本"""
    current = parse_version(current_version)
    latest = parse_version(latest_version)
    return latest > current

def get_update_cache_path():
    """获取更新检查缓存路径"""
    cache_dir = get_cache_folder()
    return os.path.join(cache_dir, "update_check.json")

def should_prompt_update(latest_version):
    """是否需要提示更新"""
    try:
        path = get_update_cache_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            last_version = data.get('last_version', '')
            last_time = float(data.get('last_time', 0))
            now = time.time()
            if latest_version == last_version and (now - last_time) < 86400:
                return False
        return True
    except:
        return True

def save_update_prompt(latest_version):
    """保存更新提示记录"""
    try:
        path = get_update_cache_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'last_version': latest_version, 'last_time': time.time()}, f)
    except:
        pass

def show_update_notification(latest_version, update_url, release_date=None, release_notes=None):
    """显示更新提示框"""
    win = tk.Toplevel()
    win.title("发现新版本")
    win.geometry("520x420")
    win.resizable(False, False)
    tk.Label(win, text=f"发现新版本 {latest_version}", font=("微软雅黑", 13, "bold")).pack(pady=(12, 4))
    if release_date:
        tk.Label(win, text=f"发布日期: {release_date}", font=("微软雅黑", 10), fg="#6B7280").pack()
    frame = tk.Frame(win)
    frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    txt = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=14)
    txt.pack(fill=tk.BOTH, expand=True)
    notes = release_notes or "暂无发布说明"
    txt.insert(tk.END, notes)
    txt.config(state=tk.DISABLED)
    btns = tk.Frame(win)
    btns.pack(pady=10)
    def go_update():
        candidates = []
        if update_url:
            candidates.append(update_url)
        if FASTGIT_RELEASES_URL:
            candidates.append(FASTGIT_RELEASES_URL)
        candidates.append(GITHUB_RELEASES_URL)
        if PROXY_RELEASES_URLS:
            candidates.extend(PROXY_RELEASES_URLS)
        for u in candidates:
            if u:
                webbrowser.open(u)
                break
        save_update_prompt(latest_version)
        win.destroy()
    tk.Button(btns, text="前往更新", command=go_update, bg="#2563EB", fg="white", width=12).pack(side=tk.LEFT, padx=8)
    tk.Button(btns, text="稍后提醒", command=lambda: win.destroy(), bg="#6B7280", fg="white", width=12).pack(side=tk.LEFT, padx=8)

def check_for_updates_in_background(current_version, root):
    """在后台线程中检查更新，避免阻塞主线程"""
    def _check():
        latest_version, update_url, release_date, release_notes = check_for_updates()
        if latest_version and is_update_available(current_version, latest_version):
            if should_prompt_update(latest_version):
                root.after(0, lambda: show_update_notification(latest_version, update_url, release_date, release_notes))
                save_update_prompt(latest_version)
        else:
            print("当前已是最新版本，或检查失败")

    # 使用线程执行检查更新
    update_thread = threading.Thread(target=_check)
    update_thread.daemon = True
    update_thread.start()


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
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = (sw - 800) // 2
            y = (sh - 600) // 2
            self.root.geometry(f"800x600+{x}+{y}")
        except:
            self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#F5F7FA")

        self.font_title = ("微软雅黑", 16, "bold")
        self.font_normal = ("微软雅黑", 10)
        self.font_btn = ("微软雅黑", 10, "bold")

        # 隐藏功能：点击右上角3次显示服务器配置
        self.title_click_count = 0
        self.click_timer = None
        self.server_url_value = "http://14.18.248.25:4888"  # 默认服务器地址
        
        # 绑定标题栏点击事件（右上角点击3次显示配置）
        self.root.bind("<Button-1>", self.on_title_click)
        self.root.bind("<Button-2>", self.on_title_click)
        self.root.bind("<Button-3>", self.on_title_click)
        
        self.ifaces = get_interfaces()
        if not self.ifaces:
            messagebox.showerror("错误", "未获取到任何网卡")
            root.destroy()
            return

        self.page_main_menu()
        if not is_admin():
            tk.Label(self.root, text="当前未以管理员运行，部分系统配置不可用", bg="#FEF3C7", fg="#92400E", font=("微软雅黑", 9)).pack(fill=tk.X)
        check_for_updates_in_background(LOCAL_VERSION, self.root)

    def on_title_click(self, event):
        """检测标题栏点击，用于显示隐藏配置"""
        # 获取点击位置相对于窗口的位置
        x = event.x
        y = event.y
        window_width = self.root.winfo_width()
        
        # 点击右上角区域（宽度80以内，高度50以内）
        if x > window_width - 80 and y < 50:
            # 重置计时器
            if self.click_timer:
                self.root.after_cancel(self.click_timer)
            
            self.title_click_count += 1
            
            # 3秒内点击3次触发
            self.click_timer = self.root.after(3000, self.reset_click_count)
            
            if self.title_click_count >= 3:
                self.title_click_count = 0
                if self.click_timer:
                    self.root.after_cancel(self.click_timer)
                self.show_server_config()
        else:
            self.reset_click_count()

    def reset_click_count(self):
        """重置点击计数"""
        self.title_click_count = 0
        self.click_timer = None

    def show_server_config(self):
        """显示服务器配置界面（隐藏功能）"""
        config_window = tk.Toplevel(self.root)
        config_window.title("服务器配置")
        config_window.geometry("400x250")
        config_window.resizable(False, False)
        config_window.configure(bg="#F5F7FA")
        
        # 居中显示
        window_width = 400
        window_height = 250
        screen_width = config_window.winfo_screenwidth()
        screen_height = config_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        config_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        tk.Label(config_window, text="服务器配置", font=("微软雅黑", 14, "bold"), 
                bg="#2F6FED", fg="white", pady=10).pack(fill=tk.X)
        
        card = tk.Frame(config_window, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        tk.Label(card, text="服务器地址:", bg="white", font=("微软雅黑", 11)).pack(anchor="w", pady=(10, 5))
        
        server_url_entry = tk.Entry(card, width=40, font=("微软雅黑", 10))
        server_url_entry.pack(fill=tk.X, pady=5)
        server_url_entry.insert(0, self.server_url_value)
        
        tk.Label(card, text="示例: http://192.168.1.100:8080", bg="white", 
                fg="#6B7280", font=("微软雅黑", 9)).pack(anchor="w", pady=(0, 20))
        
        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=20)
        
        def save_config():
            new_url = server_url_entry.get().strip()
            if new_url:
                self.server_url_value = new_url
                messagebox.showinfo("成功", f"服务器地址已保存:\n{new_url}")
                config_window.destroy()
            else:
                messagebox.showwarning("警告", "服务器地址不能为空")
        
        tk.Button(btn_frame, text="保存", command=save_config,
                 bg="#16A34A", fg="white", font=("微软雅黑", 11), width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="返回", command=config_window.destroy,
                 bg="#6B7280", fg="white", font=("微软雅黑", 11), width=12).pack(side=tk.LEFT, padx=10)

    # 创建按钮组件
    def create_button(self, parent, text, command, width=24, height=2, color="#2563EB"):
        tk.Button(parent, text=text, font=self.font_btn, bg=color, fg="white", width=width, height=height, command=command).pack(pady=15)

    def create_button_grid(self, parent, text, command, row, column, color="#2563EB"):
        btn = tk.Button(parent, text=text, font=self.font_btn, bg=color, fg="white", width=22, height=2, command=command)
        btn.grid(row=row, column=column, padx=12, pady=12, sticky="ew")

    def create_scrollable(self, parent):
        container = tk.Frame(parent, bg="white")
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        inner = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        def on_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_config)
        def on_mousewheel(event):
            delta = 1 if event.delta > 0 else -1
            canvas.yview_scroll(-delta, "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        return inner

    # 创建标签组件
    def create_label(self, parent, text, font=("微软雅黑", 10, "bold"), pady=10):
        tk.Label(parent, text=text, font=font, bg="white").pack(anchor="w", padx=15, pady=pady)

    # ---------- 主菜单页面 ----------
    def page_main_menu(self):
        self.clear()
        tk.Label(self.root, text="医保网络配置工具", font=self.font_title, bg="#2F6FED", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

        tk.Label(card, text="请选择配置模式", font=("微软雅黑", 13, "bold"), bg="white").pack(pady=(20, 10))
        buttons = tk.Frame(card, bg="white")
        buttons.pack(fill=tk.X, padx=10, pady=10)
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)
        self.create_button_grid(buttons, "🔍 医保网络检测", self.page_medical_network_check, 0, 0, color="#16A34A")
        self.create_button_grid(buttons, "🔄 检查更新", self.manual_check_update, 0, 1, color="#2563EB")
        self.create_button_grid(buttons, "🌐 双WAN配置（路由器）", self.page_dual_wan, 1, 0, color="#7C3AED")
        self.create_button_grid(buttons, "💻 单机配置（直连）", self.page_standalone_menu, 1, 1, color="#2563EB")
        self.create_button_grid(buttons, "🛡️ 防护软件", self.page_security_software, 2, 0, color="#2563EB")

    def manual_check_update(self):
        if not requests:
            messagebox.showwarning("提示", "网络模块未安装，无法检查更新")
            return
        win = tk.Toplevel(self.root)
        win.title("检查更新中")
        win.geometry("360x120")
        win.resizable(False, False)
        tk.Label(win, text="正在检查更新，请稍候...", font=("微软雅黑", 10)).pack(pady=(15, 8))
        pb = ttk.Progressbar(win, mode="indeterminate", length=300)
        pb.pack(pady=8, padx=20)
        pb.start(10)
        def on_done(result):
            try:
                latest_version, update_url, release_date, release_notes = result
                if latest_version and is_update_available(LOCAL_VERSION, latest_version):
                    show_update_notification(latest_version, update_url, release_date, release_notes)
                else:
                    messagebox.showinfo("更新检查", "当前已是最新版本或检查失败")
            finally:
                pb.stop()
                win.destroy()
        def on_error(e):
            try:
                messagebox.showerror("错误", f"检查更新失败: {e}")
            finally:
                pb.stop()
                win.destroy()
        run_in_thread(check_for_updates, on_done=on_done, on_error=on_error)

    # ---------- 防护软件下载页面 ----------
    def page_security_software(self):
        """防护软件介绍和下载页面"""
        self.clear()
        tk.Label(self.root, text="防护软件", font=self.font_title, bg="#2563EB", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=30, pady=30, fill=tk.BOTH, expand=True)

        # 返回按钮
        top_btn_frame = tk.Frame(card, bg="white")
        top_btn_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Button(top_btn_frame, text="← 返回", command=self.page_main_menu,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=10).pack(side=tk.LEFT)

        # 防护软件介绍
        tk.Label(card, text="医保安全防护软件", font=("微软雅黑", 14, "bold"), bg="white").pack(pady=(10, 5))
        tk.Label(card, text="保护您的医保系统安全", font=("微软雅黑", 11), bg="white", fg="#6B7280").pack(pady=(0, 20))

        # 介绍说明
        info_frame = tk.LabelFrame(card, text="软件说明", font=("微软雅黑", 10, "bold"), bg="white", padx=15, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(info_frame, text="• 保护医保系统网络安全\n• 防止恶意程序入侵\n• 确保数据传输安全", 
                bg="white", font=("微软雅黑", 10), justify=tk.LEFT, anchor="w").pack(anchor="w", pady=5)

        # 下载按钮区域
        download_frame = tk.LabelFrame(card, text="请选择您的网络类型下载", font=("微软雅黑", 11, "bold"), bg="white", padx=20, pady=15)
        download_frame.pack(fill=tk.X, padx=10, pady=20)

        def download_telecom():
            """下载电信专线版本"""
            telecom_url = "http://photo.cxsdwan.com:40072/share/73591412"
            webbrowser.open(telecom_url)
            messagebox.showinfo("下载提示", "正在打开电信专线下载页面...\n如果下载未开始，请检查您的网络连接")

        def download_unicom():
            """下载联通专线版本"""
            unicom_url = "http://file.cxsdwan.com:40072/s/865s98"
            webbrowser.open(unicom_url)
            messagebox.showinfo("下载提示", "正在打开联通专线下载页面...\n如果下载未开始，请检查您的网络连接")

        # 电信下载按钮
        telecom_frame = tk.Frame(download_frame, bg="white")
        telecom_frame.pack(fill=tk.X, pady=10)
        tk.Label(telecom_frame, text="电信专线用户", bg="white", font=("微软雅黑", 11), width=15, anchor="w").pack(side=tk.LEFT)
        tk.Button(telecom_frame, text="⬇️ 点击下载", command=download_telecom,
                 bg="#2563EB", fg="white", font=("微软雅黑", 10, "bold"), width=15, height=1).pack(side=tk.LEFT, padx=10)

        # 联通下载按钮
        unicom_frame = tk.Frame(download_frame, bg="white")
        unicom_frame.pack(fill=tk.X, pady=10)
        tk.Label(unicom_frame, text="联通专线用户", bg="white", font=("微软雅黑", 11), width=15, anchor="w").pack(side=tk.LEFT)
        tk.Button(unicom_frame, text="⬇️ 点击下载", command=download_unicom,
                 bg="#16A34A", fg="white", font=("微软雅黑", 10, "bold"), width=15, height=1).pack(side=tk.LEFT, padx=10)

        # 注意事项
        note_frame = tk.LabelFrame(card, text="注意事项", font=("微软雅黑", 10, "bold"), bg="white", padx=15, pady=10)
        note_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(note_frame, text="• 下载后请运行安装程序并按提示完成安装\n• 安装过程可能需要管理员权限\n• 如遇到问题，请联系技术支持", 
                bg="white", font=("微软雅黑", 9), fg="#6B7280", justify=tk.LEFT, anchor="w").pack(anchor="w", pady=5)

    # ---------- 医保网络检测页面 ----------
    def page_medical_network_check(self):
        self.clear()
        tk.Label(self.root, text="医保网络检测", font=self.font_title, bg="#16A34A", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=30, pady=30, fill=tk.BOTH, expand=True)
        content = self.create_scrollable(card)

        # 返回按钮
        top_btn_frame = tk.Frame(content, bg="white")
        top_btn_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Button(top_btn_frame, text="← 返回", command=self.page_main_menu,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=10).pack(side=tk.LEFT)

        # 检测结果标题
        tk.Label(content, text="正在检测医保网络连通性...", font=("微软雅黑", 12, "bold"), bg="white").pack(pady=(10, 20))

        # 创建结果展示区域
        result_frame = tk.LabelFrame(content, text="检测结果", font=("微软雅黑", 11, "bold"), bg="white", padx=15, pady=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 检测项1：ping 10.35.128.1
        ping_frame = tk.Frame(result_frame, bg="white")
        ping_frame.pack(fill=tk.X, pady=10)
        tk.Label(ping_frame, text="医保网关 (10.35.128.1):", width=30, bg="white", font=("微软雅黑", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        ping_status = tk.Label(ping_frame, text="检测中...", bg="white", fg="#F59E0B", font=("微软雅黑", 10))
        ping_status.pack(side=tk.LEFT, padx=10)

        # 检测项2：hisips.shx.hsip.gov.cn
        hisips_frame = tk.Frame(result_frame, bg="white")
        hisips_frame.pack(fill=tk.X, pady=10)
        tk.Label(hisips_frame, text="两定系统 (hisips):", width=30, bg="white", font=("微软雅黑", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        hisips_status = tk.Label(hisips_frame, text="检测中...", bg="white", fg="#F59E0B", font=("微软雅黑", 10))
        hisips_status.pack(side=tk.LEFT, padx=10)

        # 检测项3：fms.shx.hsip.gov.cn
        fms_frame = tk.Frame(result_frame, bg="white")
        fms_frame.pack(fill=tk.X, pady=10)
        tk.Label(fms_frame, text="费用监管系统 (fms):", width=30, bg="white", font=("微软雅黑", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        fms_status = tk.Label(fms_frame, text="检测中...", bg="white", fg="#F59E0B", font=("微软雅黑", 10))
        fms_status.pack(side=tk.LEFT, padx=10)

        # 检测项4：cts-svc.shx.hsip.gov.cn
        cts_frame = tk.Frame(result_frame, bg="white")
        cts_frame.pack(fill=tk.X, pady=10)
        tk.Label(cts_frame, text="综合服务系统 (cts-svc):", width=30, bg="white", font=("微软雅黑", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        cts_status = tk.Label(cts_frame, text="检测中...", bg="white", fg="#F59E0B", font=("微软雅黑", 10))
        cts_status.pack(side=tk.LEFT, padx=10)

        # 检测项5：防护软件
        agent_frame = tk.Frame(result_frame, bg="white")
        agent_frame.pack(fill=tk.X, pady=10)
        tk.Label(agent_frame, text="防护软件 (IsAgent):", width=30, bg="white", font=("微软雅黑", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        agent_status = tk.Label(agent_frame, text="检测中...", bg="white", fg="#F59E0B", font=("微软雅黑", 10))
        agent_status.pack(side=tk.LEFT, padx=10)

        # 详细信息显示区域
        detail_frame = tk.LabelFrame(content, text="详细信息", font=("微软雅黑", 10, "bold"), bg="white", padx=10, pady=10)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, font=("微软雅黑", 9), height=8)
        detail_text.pack(fill=tk.BOTH, expand=True)

        # 按钮区域
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(pady=15)
        
        refresh_btn = tk.Button(btn_frame, text="🔄 重新检测", command=self.page_medical_network_check,
                               bg="#2563EB", fg="white", font=("微软雅黑", 10, "bold"), width=15, height=2)
        refresh_btn.pack(side=tk.LEFT, padx=10)
        
        # 防护软件快捷按钮（默认隐藏，检测后根据状态显示）
        self.agent_download_btn = tk.Button(btn_frame, text="⬇️ 下载防护软件", command=self.page_security_software,
                                           bg="#DC2626", fg="white", font=("微软雅黑", 10, "bold"), width=15, height=2)
        self.agent_download_btn.pack(side=tk.LEFT, padx=10)
        self.agent_download_btn.pack_forget()  # 初始隐藏

        # 异步执行检测
        def run_checks():
            detail_text.insert(tk.END, f"开始检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            detail_text.insert(tk.END, "=" * 60 + "\n\n")
            
            # 1. ping 10.35.128.1
            detail_text.insert(tk.END, "【检测1】ping 医保网关 10.35.128.1\n")
            ping_success, ping_msg = ping_host("10.35.128.1", count=4)
            if ping_success:
                ping_status.config(text=f"✓ 连通 ({ping_msg})", fg="#16A34A")
                detail_text.insert(tk.END, f"结果: ✓ 成功 - {ping_msg}\n\n")
            else:
                ping_status.config(text=f"✗ 不通 ({ping_msg})", fg="#EF4444")
                detail_text.insert(tk.END, f"结果: ✗ 失败 - {ping_msg}\n\n")
            
            # 2. hisips.shx.hsip.gov.cn
            detail_text.insert(tk.END, "【检测2】两定系统 hisips.shx.hsip.gov.cn\n")
            hisips_ok = test_host_connectivity("hisips.shx.hsip.gov.cn", port=80, timeout=5)
            if hisips_ok:
                hisips_status.config(text="✓ 可访问", fg="#16A34A")
                detail_text.insert(tk.END, "结果: ✓ 可访问\n\n")
            else:
                hisips_status.config(text="✗ 无法访问", fg="#EF4444")
                detail_text.insert(tk.END, "结果: ✗ 无法访问\n\n")
            
            # 3. fms.shx.hsip.gov.cn
            detail_text.insert(tk.END, "【检测3】费用监管系统 fms.shx.hsip.gov.cn\n")
            fms_ok = test_host_connectivity("fms.shx.hsip.gov.cn", port=80, timeout=5)
            if fms_ok:
                fms_status.config(text="✓ 可访问", fg="#16A34A")
                detail_text.insert(tk.END, "结果: ✓ 可访问\n\n")
            else:
                fms_status.config(text="✗ 无法访问", fg="#EF4444")
                detail_text.insert(tk.END, "结果: ✗ 无法访问\n\n")
            
            # 4. cts-svc.shx.hsip.gov.cn
            detail_text.insert(tk.END, "【检测4】综合服务系统 cts-svc.shx.hsip.gov.cn\n")
            cts_ok = test_host_connectivity("cts-svc.shx.hsip.gov.cn", port=80, timeout=5)
            if cts_ok:
                cts_status.config(text="✓ 可访问", fg="#16A34A")
                detail_text.insert(tk.END, "结果: ✓ 可访问\n\n")
            else:
                cts_status.config(text="✗ 无法访问", fg="#EF4444")
                detail_text.insert(tk.END, "结果: ✗ 无法访问\n\n")
            
            # 5. 防护软件检测
            agent_path = r"C:\Windows\SysWOW64\IsAgent"
            agent_exists = os.path.exists(agent_path)
            detail_text.insert(tk.END, "【检测5】防护软件 IsAgent\n")
            if agent_exists:
                agent_status.config(text="✓ 已安装", fg="#16A34A")
                detail_text.insert(tk.END, f"结果: ✓ 已安装 ({agent_path})\n\n")
                # 隐藏下载按钮
                root.after(0, lambda: self.agent_download_btn.pack_forget())
            else:
                agent_status.config(text="✗ 未安装", fg="#EF4444")
                detail_text.insert(tk.END, f"结果: ✗ 未安装 ({agent_path})\n\n")
                # 显示下载按钮
                root.after(0, lambda: self.agent_download_btn.pack(side=tk.LEFT, padx=10))
            
            # 总结
            detail_text.insert(tk.END, "=" * 60 + "\n")
            all_ok = ping_success and hisips_ok and fms_ok and cts_ok and agent_exists
            if all_ok:
                detail_text.insert(tk.END, "✓ 所有检测项通过，医保网络正常！\n")
            else:
                detail_text.insert(tk.END, "⚠ 部分检测项未通过，请检查网络配置\n")
                if not agent_exists:
                    detail_text.insert(tk.END, "建议：请下载安装防护软件以确保医保网络正常访问！\n")
            
            detail_text.see(tk.END)
        
        # 在后台线程运行检测
        run_in_thread(run_checks)

    # ---------- 双WAN配置页面 ----------
    def page_dual_wan(self):
        self.clear()
        tk.Label(self.root, text="双WAN配置", font=self.font_title, bg="#7C3AED", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=30, pady=30, fill=tk.BOTH, expand=True)

        # 顶部按钮区域
        top_btn_frame = tk.Frame(card, bg="white")
        top_btn_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Button(top_btn_frame, text="← 返回", command=self.page_main_menu,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=10).pack(side=tk.LEFT)

        # 创建左右分栏
        content_frame = tk.Frame(card, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 左侧：向日葵远程控制
        left_frame = tk.LabelFrame(content_frame, text="向日葵远程控制", font=("微软雅黑", 11, "bold"), bg="white", padx=15, pady=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        is_installed, install_path = check_sunflower_installed()

        if is_installed:
            tk.Label(left_frame, text=f"✓ 向日葵已安装\n路径: {install_path}", 
                    bg="white", fg="#16A34A", font=("微软雅黑", 10)).pack(pady=10)
            tk.Button(left_frame, text="启动向日葵", command=self.launch_sunflower,
                     bg="#16A34A", fg="white", font=("微软雅黑", 10), width=15).pack(pady=10)
        else:
            tk.Label(left_frame, text="⚠ 向日葵未安装", 
                    bg="white", fg="#F59E0B", font=("微软雅黑", 10)).pack(pady=10)
            tk.Label(left_frame, text="需要使用向日葵远程协助进行路由器配置", 
                    bg="white", font=("微软雅黑", 10)).pack(pady=5)
            
            def download_and_notify():
                if download_sunflower():
                    messagebox.showinfo("下载", "已打开浏览器下载向日葵，请下载并安装后重启本程序")
                else:
                    messagebox.showerror("错误", "无法打开浏览器，请手动访问:\nhttps://down.oray.com/sunlogin/windows/SunloginClient_ng.exe")
            
            tk.Button(left_frame, text="立即下载向日葵", command=download_and_notify,
                     bg="#F59E0B", fg="white", font=("微软雅黑", 10), width=15).pack(pady=10)

        # 路由器账号配置
        tk.Label(left_frame, text="请输入路由器管理账号密码:", bg="white", font=("微软雅黑", 10)).pack(anchor="w", pady=(20, 10))

        router_ip_frame = tk.Frame(left_frame, bg="white")
        router_ip_frame.pack(fill=tk.X, pady=3)
        tk.Label(router_ip_frame, text="路由器IP:", width=10, bg="white").pack(side=tk.LEFT)
        self.router_ip = tk.Entry(router_ip_frame, width=20)
        self.router_ip.pack(side=tk.LEFT, padx=5)
        # 自动获取网关IP
        gateway = get_default_gateway()
        if gateway:
            self.router_ip.insert(0, gateway)
            tk.Label(router_ip_frame, text="✓ 已自动获取", bg="white", fg="#16A34A", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        else:
            self.router_ip.insert(0, "192.168.1.1")
            tk.Label(router_ip_frame, text="未检测到网关，请手动输入", bg="white", fg="#F59E0B", font=("微软雅黑", 9)).pack(side=tk.LEFT)

        router_user_frame = tk.Frame(left_frame, bg="white")
        router_user_frame.pack(fill=tk.X, pady=3)
        tk.Label(router_user_frame, text="管理账号:", width=10, bg="white").pack(side=tk.LEFT)
        self.router_user = tk.Entry(router_user_frame, width=20)
        self.router_user.pack(side=tk.LEFT, padx=5)
        self.router_user.insert(0, "admin")

        router_pass_frame = tk.Frame(left_frame, bg="white")
        router_pass_frame.pack(fill=tk.X, pady=3)
        tk.Label(router_pass_frame, text="管理密码:", width=10, bg="white").pack(side=tk.LEFT)
        self.router_pass = tk.Entry(router_pass_frame, width=20, show="*")
        self.router_pass.pack(side=tk.LEFT, padx=5)

        tk.Label(left_frame, text="提示: 配置前请确保已登录路由器管理界面", 
                bg="white", fg="#6B7280", font=("微软雅黑", 9)).pack(anchor="w", pady=(15, 0))

        # 一键修改MTU按钮
        mtu_frame = tk.Frame(left_frame, bg="white")
        mtu_frame.pack(fill=tk.X, pady=(10, 5))
        tk.Label(mtu_frame, text="系统设置", bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", pady=(10, 5))
        tk.Button(mtu_frame, text="⚡ 一键修改MTU=1300", command=self.set_all_mtu,
                 bg="#2563EB", fg="white", font=("微软雅黑", 10), width=20, height=1).pack(anchor="w", pady=5)

        # 右侧：配置信息展示（从服务器获取）
        right_frame = tk.LabelFrame(content_frame, text="配置信息展示", font=("微软雅黑", 11, "bold"), bg="white", padx=15, pady=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 服务器信息显示（点击标题栏3次可修改）
        server_info_frame = tk.Frame(right_frame, bg="white")
        server_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # tk.Label(server_info_frame, text="服务器:", bg="white", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        # self.server_display = tk.Label(server_info_frame, text=self.server_url_value,
        #                               bg="white", fg="#2563EB", font=("微软雅黑", 9))
        # self.server_display.pack(side=tk.LEFT, padx=5)

        #隐藏配置接口
        # tk.Label(server_info_frame, text="  (点击标题栏3次修改)", bg="white",
        #         fg="#9CA3AF", font=("微软雅黑", 8)).pack(side=tk.LEFT)

        # 服务器管理按钮
        server_btn_frame = tk.Frame(right_frame, bg="white")
        server_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(server_btn_frame, text="刷新信息", command=self.page_info_display,
                 bg="#2563EB", fg="white", font=("微软雅黑", 9), width=10).pack(side=tk.LEFT, padx=(0, 5))
        # tk.Button(server_btn_frame, text="打开服务器", command=self.open_server_url,
        #          bg="#16A34A", fg="white", font=("微软雅黑", 9), width=10).pack(side=tk.LEFT, padx=(0, 5))

        # 服务器状态
        self.server_status = tk.Label(right_frame, text="未检测到服务器", bg="white", fg="#6B7280", font=("微软雅黑", 9))
        self.server_status.pack(anchor="w", pady=(0, 10))

        # 信息展示区域
        self.info_notebook = tk.ttk.Notebook(right_frame)
        self.info_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 初始化信息展示
        self.page_info_display()

    def launch_sunflower(self):
        """启动向日葵远程"""
        is_installed, install_path = check_sunflower_installed()
        if is_installed:
            try:
                subprocess.Popen(f'"{install_path}"', shell=True)
                messagebox.showinfo("提示", "向日葵已启动")
            except Exception as e:
                messagebox.showerror("错误", f"启动向日葵失败: {str(e)}")
        else:
            messagebox.showwarning("提示", "向日葵未安装，请先下载安装")

    def set_all_mtu(self):
        """一键设置所有网卡MTU=1300"""
        if not is_admin():
            messagebox.showerror("权限不足", "请以管理员身份运行后再执行此操作")
            return
        def task():
            results = set_all_mtu(1300)
            return results

        def on_done(results):
            result_text = "\n".join(results) if results else "配置完成"
            messagebox.showinfo("MTU设置完成", f"设置结果:\n{result_text}")

        def on_error(e):
            messagebox.showerror("错误", f"设置失败: {str(e)}")

        run_in_thread(task, on_done, on_error)

    def open_server_url(self):
        """打开服务器管理页面"""
        webbrowser.open(self.server_url_value)
    
    def page_info_display(self):
        """从服务器下载并展示配置信息（自动下载到本地）"""
        # 检查服务器状态
        is_connected, status_data = check_server_status(self.server_url_value) if SERVER_AVAILABLE else (False, None)
        
        # 安全检查：如果server_status存在才更新
        if hasattr(self, 'server_status') and self.server_status:
            if is_connected:
                self.server_status.config(
                    text=f"✓ 已连接服务器 (端口: {status_data.get('port', 8080)}, 文件数: {status_data.get('files_count', 0)})",
                    fg="#16A34A"
                )
            else:
                self.server_status.config(
                    text=f"⚠ 未检测到服务器: {self.server_url_value}",
                    fg="#F59E0B"
                )
        
        # 清除现有的标签页
        for tab in self.info_notebook.tabs():
            self.info_notebook.forget(tab)
        
        if not is_connected:
            # 服务器未连接，显示提示
            empty_frame = tk.Frame(self.info_notebook, bg="white")
            self.info_notebook.add(empty_frame, text="提示")
            
            tk.Label(empty_frame, text="服务器未连接", bg="white", fg="#F59E0B", font=("微软雅黑", 14)).pack(pady=30)
            tk.Label(empty_frame, text=f"当前服务器: {self.server_url_value}", bg="white", fg="#666", font=("微软雅黑", 12)).pack(pady=10)
            tk.Label(empty_frame, text="请检查服务器地址是否正确，或服务器是否已启动", bg="white", fg="#666", font=("微软雅黑", 10)).pack(pady=5)
            return
        
        # 清空本地缓存并重新下载
        clear_cache()
        
        # 从服务器获取文件列表
        files = fetch_server_files(self.server_url_value) if SERVER_AVAILABLE else []
        
        if not files:
            # 无文件
            empty_frame = tk.Frame(self.info_notebook, bg="white")
            self.info_notebook.add(empty_frame, text="提示")
            
            tk.Label(empty_frame, text="服务器无配置文件", bg="white", fg="#6B7280", font=("微软雅黑", 12)).pack(pady=30)
            tk.Label(empty_frame, text="请在服务器管理页面上传配置文件", bg="white", fg="#666", font=("微软雅黑", 10)).pack(pady=10)
            return
        
        # 获取文件扩展名
        def get_file_ext(filename):
            return os.path.splitext(filename)[1].lower()
        
        # 创建标签页展示文件内容
        for file_info in files:
            filename = file_info.get('name', '')
            file_ext = get_file_ext(filename)
            
            frame = tk.Frame(self.info_notebook, bg="white")
            self.info_notebook.add(frame, text=filename[:10] + "..." if len(filename) > 10 else filename)
            
            # 下载文件到本地
            local_path = download_file_to_cache(self.server_url_value, filename) if SERVER_AVAILABLE else None
            
            if file_ext in ['.txt', '.md', '.py', '.json', '.xml', '.html', '.css', '.js', '.log']:
                # 文本文件 - 在GUI中直接显示
                if local_path and os.path.exists(local_path):
                    try:
                        with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except:
                        content = "无法读取文件内容"
                else:
                    content = (fetch_file_content(self.server_url_value, filename) if SERVER_AVAILABLE else None) or "下载失败"
                
                # 显示文本
                text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("微软雅黑", 10))
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, content)
                text_widget.config(state=tk.DISABLED)
                
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                # 图片文件 - 在GUI中显示
                if local_path and os.path.exists(local_path) and Image is not None:
                    try:
                        # 加载图片
                        img = Image.open(local_path)
                        
                        # 计算缩放尺寸
                        max_width = 650
                        max_height = 450
                        width, height = img.size
                        ratio = min(max_width / width, max_height / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # 显示图片
                        label = tk.Label(frame, image=photo, bg="white")
                        label.image = photo  # 保持引用
                        label.pack(padx=10, pady=10)
                        
                    except Exception as e:
                        tk.Label(frame, text=f"无法加载图片: {str(e)}", bg="white", fg="#EF4444").pack(pady=30)
                else:
                    tk.Label(frame, text="图片加载失败或图像库未安装", bg="white", fg="#EF4444").pack(pady=30)
            else:
                # 其他文件 - 显示文件信息
                file_size = file_info.get('size', 0)
                tk.Label(frame, text=f"文件: {filename}", bg="white", fg="#2563EB", font=("微软雅黑", 11)).pack(pady=20)
                tk.Label(frame, text=f"大小: {file_size} bytes", bg="white", fg="#666", font=("微软雅黑", 10)).pack(pady=5)

    def start_dual_wan_config(self):
        """开始双WAN配置"""
        router_ip = self.router_ip.get().strip()
        router_user = self.router_user.get().strip()
        router_pass = self.router_pass.get().strip()

        if not router_pass:
            messagebox.showwarning("提示", "请输入路由器管理密码")
            return

        def task():
            results = []
            
            # 一键设置所有网卡MTU=1300（移除勾选，直接应用）
            try:
                mtu_results = set_all_mtu(1300)
                results.extend(mtu_results)
            except Exception as e:
                results.append(f"✗ MTU设置失败: {str(e)}")
            
            # 获取当前路由配置（单路由配置）
            try:
                route_output = subprocess.check_output(
                    'route print -4',
                    shell=True,
                    encoding='gbk',
                    errors='ignore'
                )
                # 检查是否存在10.0.0.0路由
                if '10.0.0.0' in route_output:
                    results.append("\n【单路由配置信息】")
                    for line in route_output.splitlines():
                        if '10.0.0.0' in line:
                            results.append(f"  {line.strip()}")
                else:
                    results.append("\n【单路由配置】未检测到10.0.0.0路由")
            except Exception as e:
                results.append(f"\n✗ 获取路由信息失败: {str(e)}")
            
            return results

        def on_done(results):
            result_text = "\n".join(results) if results else "配置完成"
            messagebox.showinfo("双WAN配置完成", f"配置结果:\n{result_text}\n\n请使用向日葵远程连接路由器进行WAN口配置\n路由器IP: {router_ip}\n账号: {router_user}")

        def on_error(e):
            messagebox.showerror("错误", f"配置失败: {str(e)}")

        run_in_thread(task, on_done, on_error)

    # ---------- 单机配置子菜单 ----------
    def page_standalone_menu(self):
        self.clear()
        tk.Label(self.root, text="单机配置", font=self.font_title, bg="#2563EB", fg="white", pady=14).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

        # 返回按钮
        top_btn_frame = tk.Frame(card, bg="white")
        top_btn_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Button(top_btn_frame, text="← 返回", command=self.page_main_menu,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=10).pack(side=tk.LEFT)

        tk.Label(card, text="请选择功能", font=("微软雅黑", 13, "bold"), bg="white").pack(pady=30)

        self.create_button(card, "🧾 仅补全 hosts 文件", self.page_hosts_only, color="#16A34A")
        self.create_button(card, "🌐 IP / MTU / 路由配置", self.page_select, color="#2563EB")

    # ---------- hosts 补全页面 ----------
    def page_hosts_only(self):
        self.clear()
        tk.Label(self.root, text="hosts 文件补全", font=self.font_title, bg="#16A34A", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 先检查hosts状态
        is_complete, missing, existing = check_hosts_status()
        
        status_frame = tk.LabelFrame(card, text="hosts 文件检查结果", font=("微软雅黑", 11, "bold"), bg="white", padx=15, pady=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))

        if is_complete:
            tk.Label(status_frame, text="✓ hosts 文件已完善", 
                    bg="white", fg="#16A34A", font=("微软雅黑", 11)).pack(pady=10)
            tk.Label(status_frame, text="所有医保系统条目已存在", 
                    bg="white", font=("微软雅黑", 10)).pack(pady=5)
        else:
            tk.Label(status_frame, text="⚠ hosts 文件不完整", 
                    bg="white", fg="#F59E0B", font=("微软雅黑", 11)).pack(pady=10)
            
            if existing:
                tk.Label(status_frame, text="已存在的条目:", bg="white", font=("微软雅黑", 10)).pack(anchor="w", pady=(10, 5))
                for entry in existing:
                    tk.Label(status_frame, text=f"  ✓ {entry}", bg="white", fg="#16A34A", font=("微软雅黑", 9)).pack(anchor="w")
            
            if missing:
                tk.Label(status_frame, text="缺失的条目:", bg="white", font=("微软雅黑", 10)).pack(anchor="w", pady=(10, 5))
                for entry in missing:
                    tk.Label(status_frame, text=f"  ✗ {entry}", bg="white", fg="#EF4444", font=("微软雅黑", 9)).pack(anchor="w")

        status_label = tk.Label(card, text="等待操作", bg="white", font=("微软雅黑", 10))
        status_label.pack(pady=20)

        def do_hosts():
            is_complete_now, missing_now, _ = check_hosts_status()
            if is_complete_now:
                return "hosts 文件已完善，无需修改"
            
            added = modify_hosts()
            if added:
                return f"已补全 {len(added)} 个条目:\n" + "\n".join(added)
            return "hosts 文件无变化"

        def on_done(msg):
            status_label.config(text=msg)
            messagebox.showinfo("完成", msg)
            # 刷新状态显示
            self.page_hosts_only()

        def check_and_done():
            is_complete_check, _, _ = check_hosts_status()
            if is_complete_check:
                status_label.config(text="✓ hosts 文件已完善")
                messagebox.showinfo("完成", "hosts 文件已完善，无需修改")
            else:
                run_in_thread(do_hosts, on_done)

        def open_hosts_file():
            """打开hosts文件位置"""
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            try:
                # 选择在资源管理器中打开
                subprocess.Popen(f'explorer /select,"{hosts_path}"')
                messagebox.showinfo("提示", f"已打开hosts文件位置:\n{hosts_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开hosts文件: {str(e)}\n\n请手动访问:\n{hosts_path}")

        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="📂 打开文件位置", command=open_hosts_file,
                 bg="#7C3AED", fg="white", font=("微软雅黑", 10, "bold"), width=15, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="检查并补全", command=check_and_done,
                 bg="#16A34A", fg="white", font=("微软雅黑", 11, "bold"), width=15, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="返回", command=self.page_standalone_menu,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=12, height=2).pack(side=tk.LEFT, padx=5)

    # ---------- 网卡选择页面 ----------
    def page_select(self):
        self.clear()
        tk.Label(self.root, text="医保网络配置工具", font=self.font_title, bg="#2563EB", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        tk.Label(card, text="请选择需要配置的网卡", font=("微软雅黑", 11, "bold"), bg="white").pack(anchor="w", padx=15, pady=(15, 5))

        self.lb = tk.Listbox(card, width=95, height=8, font=self.font_normal)
        for name, ip in self.ifaces:
            self.lb.insert(tk.END, f"{name}    [{ip}]")
        self.lb.pack(padx=15, pady=5)

        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="下一步", command=self.page_config,
                 bg="#2563EB", fg="white", font=self.font_btn, width=14, height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="返回", command=self.page_standalone_menu,
                 bg="#6B7280", fg="white", font=self.font_btn, width=12, height=2).pack(side=tk.LEFT, padx=10)

    # ---------- 配置页面 ----------
    def page_config(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择网卡")
            return

        self.iface = self.ifaces[sel[0]][0]
        self.clear()

        tk.Label(self.root, text="网络参数配置", font=self.font_title, bg="#2563EB", fg="white", pady=12).pack(fill=tk.X)

        card = tk.Frame(self.root, bg="white")
        card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 返回按钮
        top_btn_frame = tk.Frame(card, bg="white")
        top_btn_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Button(top_btn_frame, text="← 返回", command=self.page_select,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=10).pack(side=tk.LEFT)

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
        if not is_admin():
            messagebox.showerror("权限不足", "请以管理员身份运行后再执行系统配置")
            return
        ip = self.ip.get().strip()
        mask = self.mask.get().strip()
        dns = self.dns.get().strip()

        # 创建进度对话框
        progress_window = tk.Toplevel(self.root)
        progress_window.title("配置中...")
        progress_window.geometry("350x120")
        progress_window.resizable(False, False)
        progress_window.configure(bg="white")
        
        # 居中
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        x = (screen_width - 350) // 2
        y = (screen_height - 120) // 2
        progress_window.geometry(f"350x120+{x}+{y}")
        
        # 进度标签
        progress_label = tk.Label(progress_window, text="准备中...", bg="white", font=("微软雅黑", 10))
        progress_label.pack(pady=(15, 10))
        
        # 进度条
        self.progress_var = tk.IntVar(value=0)
        progress_bar = ttk.Progressbar(progress_window, variable=self.progress_var, maximum=100, length=300)
        progress_bar.pack(pady=10, padx=20)
        
        # 更新进度回调
        def progress_callback(current, total, message):
            percent = int((current / total) * 100)
            self.progress_var.set(percent)
            progress_label.config(text=message)
            progress_window.update()

        def task():
            missing = get_missing_items(self.iface)
            if force:
                missing = ["IP 地址", "路由", "MTU", "hosts 文件"]
            if missing:
                apply_missing_config(self.iface, ip, mask, dns, missing, progress_callback)
            return missing

        def on_done(missing):
            progress_window.destroy()
            if not missing and not force:
                messagebox.showinfo("无需配置", "配置已存在，进入校验页面")
            else:
                messagebox.showinfo("完成", "配置完成，进入校验页面")
            self.page_verify()

        def on_error(e):
            progress_window.destroy()
            messagebox.showerror("失败", str(e))

        run_in_thread(task, on_done, on_error)

    # ---------- 校验页面 ----------
    def page_verify(self):
        self.clear()
        tk.Label(self.root, text="配置校验", font=self.font_title, bg="#2563EB", fg="white", pady=12).pack(fill=tk.X)

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

        tk.Label(card, text="医保地址连通性测试", bg="white", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        hosts = ["hisips.shx.hsip.gov.cn", "fms.shx.hsip.gov.cn", "cts-svc.shx.hsip.gov.cn"]
        for h in hosts:
            ok = test_host_connectivity(h)
            lbl = tk.Label(card, text=f"{h}: {'🟢 可访问' if ok else '🔴 不可访问'}", bg="white", font=("微软雅黑", 10))
            lbl.pack(anchor="w", padx=25)

        link = tk.Label(card, text="访问医保官网", fg="#2563EB", bg="white", cursor="hand2", font=("微软雅黑", 10, "underline"))
        link.pack(anchor="w", padx=15, pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open("http://hisips.shx.hsip.gov.cn"))

        # 按钮区域
        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="返回配置", command=self.page_config,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=12, height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="关闭", command=self.root.destroy,
                 bg="#6B7280", fg="white", font=("微软雅黑", 10), width=12, height=2).pack(side=tk.LEFT, padx=10)

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    try:
        App(root)
        root.mainloop()
    except Exception as e:
        try:
            log_error(f"启动失败: {str(e)}")
        except:
            pass
        try:
            messagebox.showerror("启动失败", f"程序无法启动，请联系技术支持。\n错误信息已记录。")
        finally:
            try:
                root.destroy()
            except:
                pass
