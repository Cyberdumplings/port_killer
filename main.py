import platform
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess

# ── 配色方案 ──────────────────────────────────────────────
COLORS = {
    "primary":      "#2196F3",   # 主色调 - 蓝
    "primary_dark": "#1976D2",
    "primary_light":"#BBDEFB",
    "success":      "#4CAF50",   # 成功 - 绿
    "success_light":"#C8E6C9",
    "danger":       "#F44336",   # 危险 - 红
    "danger_light": "#FFCDD2",
    "warning":      "#FF9800",   # 警告 - 橙
    "bg":           "#F0F2F5",   # 页面背景
    "card":         "#FFFFFF",   # 卡片背景
    "text":         "#212121",   # 主文字
    "text_secondary":"#616161",  # 次要文字
    "border":       "#E0E0E0",   # 边框
    "log_bg":       "#1E1E1E",   # 日志区域背景 (暗色终端风)
    "log_fg":       "#D4D4D4",   # 日志文字
    "header_bg":    "#1565C0",   # 头部背景
}


class PortKillerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("端口占用清理工具")
        self.root.geometry("680x620")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(580, 480)

        self.system = platform.system()
        self.process_info = []

        self._setup_styles()
        self.create_widgets()

    def _setup_styles(self):
        """配置 ttk 主题样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 全局字体
        self.FONT = ("Microsoft YaHei UI", 9)
        self.FONT_BOLD = ("Microsoft YaHei UI", 9, "bold")
        self.FONT_TITLE = ("Microsoft YaHei UI", 13, "bold")
        self.FONT_MONO = ("Cascadia Code", 10)
        self.FONT_MONO = ("Consolas", 10)  # 回退

        style.configure(".", font=self.FONT, background=COLORS["bg"])

        # TLabel (默认)
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])

        # 主按钮 (检查端口)
        style.configure("Primary.TButton",
            font=self.FONT_BOLD,
            padding=(18, 8),
            background=COLORS["primary"],
            foreground="white",
            borderwidth=0,
            relief="flat",
        )
        style.map("Primary.TButton",
            background=[("active", COLORS["primary_dark"]), ("pressed", "#0D47A1")],
            foreground=[("active", "white")],
        )

        # 危险按钮 (结束进程)
        style.configure("Danger.TButton",
            font=self.FONT_BOLD,
            padding=(18, 8),
            background=COLORS["danger"],
            foreground="white",
            borderwidth=0,
            relief="flat",
        )
        style.map("Danger.TButton",
            background=[("active", "#D32F2F"), ("pressed", "#B71C1C")],
            foreground=[("active", "white")],
        )

        # 普通按钮 (清空日志)
        style.configure("Secondary.TButton",
            font=self.FONT,
            padding=(14, 7),
            background="#E0E0E0",
            foreground=COLORS["text"],
            borderwidth=0,
            relief="flat",
        )
        style.map("Secondary.TButton",
            background=[("active", "#BDBDBD"), ("pressed", "#9E9E9E")],
        )

        # LabelFrame (卡片)
        style.configure("Card.TLabelframe",
            background=COLORS["card"],
            bordercolor=COLORS["border"],
            relief="flat",
            borderwidth=1,
        )
        style.configure("Card.TLabelframe.Label",
            background=COLORS["card"],
            foreground=COLORS["text"],
            font=self.FONT_BOLD,
        )

        # Entry
        style.configure("TEntry",
            fieldbackground=COLORS["card"],
            bordercolor=COLORS["border"],
            padding=8,
            relief="flat",
        )

    # ── UI 构建 ──────────────────────────────────────────

    def create_widgets(self):
        # ── 顶部标题栏 ──
        header = tk.Frame(
            self.root, bg=COLORS["header_bg"], height=70, highlightthickness=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🔧  端口占用清理工具",
            font=("Microsoft YaHei UI", 15, "bold"),
            fg="white",
            bg=COLORS["header_bg"],
        ).pack(side="left", padx=20, pady=18)

        tk.Label(
            header,
            text=f"  {self.system}  ",
            font=("Microsoft YaHei UI", 8),
            fg="#90CAF9",  # 半透明白的等效浅蓝色
            bg=COLORS["header_bg"],
        ).pack(side="right", padx=20, pady=18)

        # ── 主内容区域 ──
        content = tk.Frame(self.root, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=12, pady=8)

        # ── 输入卡片 ──
        input_card = ttk.LabelFrame(content, text="  🎯 输入端口 ", style="Card.TLabelframe", padding=15)
        input_card.pack(fill="x", pady=(0, 8))

        input_row = tk.Frame(input_card, bg=COLORS["card"])
        input_row.pack(fill="x")

        ttk.Label(
            input_row, text="端口号  ", font=self.FONT, background=COLORS["card"]
        ).pack(side="left")

        self.port_entry = ttk.Entry(input_row, font=self.FONT_MONO, width=14)
        self.port_entry.pack(side="left", padx=(0, 10))
        self.port_entry.bind("<Return>", lambda e: self.check_port())

        self.check_btn = ttk.Button(
            input_row, text="  🔍  检查端口  ", style="Primary.TButton", command=self.check_port
        )
        self.check_btn.pack(side="left", padx=4)

        self.kill_btn = ttk.Button(
            input_row, text="  ⚡  结束进程  ", style="Danger.TButton", command=self.kill_process
        )
        self.kill_btn.pack(side="left", padx=4)

        self.clear_btn = ttk.Button(
            input_row, text="  🗑  清空日志  ", style="Secondary.TButton", command=self.clear_log
        )
        self.clear_btn.pack(side="right", padx=4)

        self.port_entry.focus_set()

        # ── 日志卡片 ──
        log_card = ttk.LabelFrame(content, text="  📋  输出日志 ", style="Card.TLabelframe", padding=10)
        log_card.pack(fill="both", expand=True, pady=(0, 8))

        self.info_text = scrolledtext.ScrolledText(
            log_card,
            height=20,
            font=self.FONT_MONO,
            bg=COLORS["log_bg"],
            fg=COLORS["log_fg"],
            insertbackground="white",
            selectbackground=COLORS["primary"],
            selectforeground="white",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            highlightthickness=0,
        )
        self.info_text.pack(fill="both", expand=True)

        # ── 配置日志颜色标签 ──
        self.info_text.tag_configure("success", foreground="#4EC9B0")
        self.info_text.tag_configure("error", foreground="#F44747")
        self.info_text.tag_configure("info", foreground="#569CD6")
        self.info_text.tag_configure("warning", foreground="#CE9178")
        self.info_text.tag_configure("highlight", foreground="#DCDCAA")
        self.info_text.tag_configure("separator", foreground="#6A6A6A")
        self.info_text.tag_configure("process", foreground="#9CDCFE", font=self.FONT_MONO)

        # ── 底部状态栏 ──
        status_frame = tk.Frame(self.root, bg=COLORS["card"], height=34)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        # 状态指示灯
        self.status_dot = tk.Canvas(
            status_frame, width=10, height=10, bg=COLORS["card"], highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(14, 4))
        self._dot = self.status_dot.create_oval(1, 1, 9, 9, fill=COLORS["success"], outline="")

        self.status_var = tk.StringVar(value="就绪")
        tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Microsoft YaHei UI", 8),
            fg=COLORS["text_secondary"],
            bg=COLORS["card"],
        ).pack(side="left")

        # 端口小提示
        self.hint_var = tk.StringVar(value="输入端口号后按回车或点击按钮  |  端口范围: 1-65535")
        tk.Label(
            status_frame,
            textvariable=self.hint_var,
            font=("Microsoft YaHei UI", 8),
            fg=COLORS["text_secondary"],
            bg=COLORS["card"],
        ).pack(side="right", padx=14)

    # ── 日志（带颜色）────────────────────────────────────

    def log(self, message, tag=None):
        """带颜色标签的日志输出"""
        start = self.info_text.index(tk.END + "-1c")
        self.info_text.insert(tk.END, message + "\n")
        end = self.info_text.index(tk.END + "-1c")
        if tag:
            self.info_text.tag_add(tag, start, end)
        self.info_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        self.info_text.delete("1.0", tk.END)
        self._set_status("idle")

    # ── 状态管理 ─────────────────────────────────────────

    def _set_status(self, state):
        """统一设置状态栏样式"""
        colors = {
            "idle":    (COLORS["success"], "就绪"),
            "working": (COLORS["warning"], "处理中…"),
            "error":   (COLORS["danger"],  "操作失败"),
            "done":    (COLORS["primary"], "操作完成"),
        }
        if state in colors:
            color, text = colors[state]
            self.status_dot.itemconfig(self._dot, fill=color)
            self.status_var.set(text)

    # ── 进程名查询 ───────────────────────────────────────

    def _get_process_name(self, pid):
        try:
            if self.system == "Windows":
                cmd = f'tasklist /FI "PID eq {pid}" /FO CSV /NH'
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    if len(parts) >= 1:
                        return parts[0].strip('"')
        except Exception:
            pass
        return "未知进程"

    # ── 端口检查 ─────────────────────────────────────────

    def _check_port_thread(self, port):
        try:
            port = int(port)
            self.process_info = []

            if self.system != "Windows":
                self.log("⚠  当前仅支持 Windows 系统", "warning")
                self._set_status("error")
                return

            cmd = f"netstat -ano | findstr :{port}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )

            if result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                seen_pids = set()
                self.log("┌─ 扫描结果 ──────────────────────────────────────────────", "separator")
                for line in lines:
                    if "LISTENING" in line:
                        parts = line.split()
                        pid = parts[-1]
                        if pid.isdigit() and pid not in seen_pids:
                            seen_pids.add(pid)
                            name = self._get_process_name(pid)
                            self.process_info.append({"pid": int(pid), "name": name})
                            self.log(f"│  🟢 LISTENING  →  [{name}]  PID: {pid}", "highlight")
                    elif "ESTABLISHED" in line:
                        parts = line.split()
                        pid = parts[-1]
                        if pid.isdigit():
                            self.log(f"│  🔵 ESTABLISHED  PID: {pid}", "separator")
                self.log("└──────────────────────────────────────────────────────────", "separator")

                if self.process_info:
                    count = len(self.process_info)
                    self.log(f"\n✓  共发现 {count} 个进程正在监听端口 {port}", "info")
                    self._set_status("done")
                else:
                    self.log(f"\n✓  端口 {port} 当前没有被任何进程监听", "success")
                    self._set_status("idle")
            else:
                self.log(f"\n✓  端口 {port} 当前没有被任何进程监听", "success")
                self._set_status("idle")

        except ValueError:
            self.log("✗  端口号格式错误", "error")
            self._set_status("error")
        except Exception as e:
            self.log(f"✗  检查出错: {e}", "error")
            self._set_status("error")

    def check_port(self):
        port = self.port_entry.get().strip()
        if not port.isdigit():
            messagebox.showerror("输入错误", "请输入一个有效的数字端口号 (1-65535)")
            return

        self.log("", "")
        self.log("═" * 60, "separator")
        self.log(f"▶  正在检查端口 {port} 的占用情况…", "info")
        self._set_status("working")

        thread = threading.Thread(target=self._check_port_thread, args=(port,))
        thread.daemon = True
        thread.start()

    # ── 结束进程 ─────────────────────────────────────────

    def kill_process(self):
        if not self.process_info:
            messagebox.showwarning("提示", "请先检查端口，且端口需被进程占用")
            return

        if len(self.process_info) == 1:
            proc = self.process_info[0]
            result = messagebox.askyesno(
                "确认结束进程",
                f"确认结束以下进程吗？\n\n"
                f"  进程名: {proc['name']}\n"
                f"  PID:    {proc['pid']}",
                icon="warning",
            )
            if result:
                self._do_kill(proc)
        else:
            self._show_process_selector()

    def _show_process_selector(self):
        """多进程选择弹窗"""
        win = tk.Toplevel(self.root)
        win.title("选择要结束的进程")
        win.geometry("440x280")
        win.configure(bg=COLORS["card"])
        win.transient(self.root)
        win.grab_set()

        # 居中
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 440) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 280) // 2
        win.geometry(f"+{x}+{y}")

        # 标题
        tk.Label(
            win,
            text=f"发现 {len(self.process_info)} 个进程占用该端口，请选择要结束的进程:",
            font=("Microsoft YaHei UI", 10, "bold"),
            fg=COLORS["text"],
            bg=COLORS["card"],
        ).pack(fill="x", padx=16, pady=(16, 8))

        # 列表
        list_frame = tk.Frame(win, bg=COLORS["border"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        listbox = tk.Listbox(
            list_frame,
            font=self.FONT_MONO,
            bg=COLORS["log_bg"],
            fg=COLORS["log_fg"],
            selectbackground=COLORS["primary"],
            selectforeground="white",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
        )
        listbox.pack(fill="both", expand=True, padx=1, pady=1)

        for i, p in enumerate(self.process_info):
            listbox.insert(tk.END, f"  [{p['name']}]   PID: {p['pid']}")
        listbox.insert(tk.END, f"  ── 全部结束 ── ({len(self.process_info)} 个进程)")
        listbox.selection_set(0)

        def on_confirm():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("提示", "请先选择一个进程", parent=win)
                return
            idx = sel[0]
            win.destroy()
            if idx == len(self.process_info):
                if messagebox.askyesno(
                    "确认全部结束",
                    f"确认结束全部 {len(self.process_info)} 个进程吗？",
                    icon="warning",
                ):
                    for proc in self.process_info:
                        self._do_kill(proc)
            else:
                proc = self.process_info[idx]
                if messagebox.askyesno(
                    "确认结束进程",
                    f"确认结束以下进程吗？\n\n  进程名: {proc['name']}\n  PID:    {proc['pid']}",
                    icon="warning",
                ):
                    self._do_kill(proc)

        listbox.bind("<Double-Button-1>", lambda e: on_confirm())

        # 按钮区
        btn_frame = tk.Frame(win, bg=COLORS["card"])
        btn_frame.pack(pady=12)

        ttk.Button(btn_frame, text="  确认  ", style="Danger.TButton", command=on_confirm).pack(
            side="left", padx=6
        )
        ttk.Button(
            btn_frame, text="  取消  ", style="Secondary.TButton", command=win.destroy
        ).pack(side="left", padx=6)

    def _do_kill(self, proc):
        pid, name = proc["pid"], proc["name"]
        self.log(f"\n⏳  正在结束进程 [{name}] (PID: {pid})…", "warning")
        self._set_status("working")

        thread = threading.Thread(target=self._kill_process_thread, args=(pid, name))
        thread.daemon = True
        thread.start()

    def _kill_process_thread(self, pid, name):
        try:
            if self.system == "Windows":
                cmd = f"taskkill /F /PID {pid}"
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.log(f"✓  进程 [{name}] (PID: {pid}) 已成功结束", "success")
                    self._set_status("idle")
                else:
                    self.log(f"✗  进程 [{name}] (PID: {pid}) 结束失败 (错误码: {result.returncode})", "error")
                    if result.stderr:
                        self.log(f"   {result.stderr.strip()}", "error")
                    self._set_status("error")
            else:
                self.log("⚠  当前仅支持 Windows 系统", "warning")
                self._set_status("error")
        except Exception as e:
            self.log(f"✗  结束进程 [{name}] (PID: {pid}) 时出错: {e}", "error")
            self._set_status("error")
        finally:
            self.process_info = [p for p in self.process_info if p["pid"] != pid]


if __name__ == "__main__":
    root = tk.Tk()
    app = PortKillerGUI(root)
    root.mainloop()
