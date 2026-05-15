import platform
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess


class PortKillerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("端口占用清理工具")
        self.root.geometry("600x500")
        self.system = platform.system()
        self.create_widgets()

    def create_widgets(self):
        # 端口号选择
        input_frame = ttk.LabelFrame(self.root, text="输入端口", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(input_frame, text="端口号:").grid(row=0, column=0, padx=5)

        self.port_entry = ttk.Entry(input_frame, width=15)
        self.port_entry.grid(row=0, column=1, padx=5)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=19, pady=5)
        self.check_btn = ttk.Button(btn_frame, text="检查端口", command=self.check_port)
        self.check_btn.pack(side="left", padx=5)

        self.kill_btn = ttk.Button(btn_frame, text="结束进程", command=self.kill_process)
        self.kill_btn.pack(side="left", padx=5)

        self.info_text = scrolledtext.ScrolledText(self.root, height=20, width=70, font=("Consolas", 10))
        self.info_text.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", padx=10, pady=5)

    def log(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.root.update()

    def _check_port_thread(self, port):
        try:
            port = int(port)
            self.process_info = None
            if self.system == "Windows":
                cmd = f"netstat -ano | findstr :{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if 'LISTENING' in line:
                            parts = line.split()
                            pid = parts[-1]
                            if pid.isdigit():
                                self.process_info = {'pid': int(pid)}
                                self.log(f"端口{port}被进程 {pid}占用")
        except Exception as e:
            self.log(f"检查端口{port}占用情况时出错: {e}")
        self.status_var.set(f"检查端口{port}占用情况完成")

    def check_port(self):
        port = self.port_entry.get().strip()
        if not port.isdigit():
            messagebox.showerror("错误", "请输入一个数字端口号")
            return
        self.log(f"\n{'=' * 79}")
        self.log(f"正在检查端口{port}占用情况")

        thread = threading.Thread(target=self._check_port_thread, args=(port,))
        thread.start()

    def kill_process(self):
        if not self.process_info:
            messagebox.showerror("警告", "没有进程占用端口")
            return
        result = messagebox.askyesno("确认", f"确认结束进程 {self.process_info['pid']} 吗？")
        if not result:
            return
        pid = self.process_info['pid']
        self.log(f"正在结束进程 {pid}")
        self.status_var.set("正在结束进程...")
        thread = threading.Thread(target=self._kill_process_thread, args=(pid,))
        thread.daemon = True
        thread.start()

    def _kill_process_thread(self, pid):
        try:
            if self.system == "Windows":
                cmd = f"taskkill /F /PID {pid}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log(f"进程 {pid} 已成功结束")

                else:
                    self.log(f"进程 {pid} 结束失败")
                    self.log(f"错误码: {result.returncode}")
                    self.log(f"错误信息: {result.stderr}")
        except Exception as e:
            self.log(f"结束进程 {pid}时出错: {e}")
            self.status_var.set(f"结束进程 {pid}失败")

        self.status_var.set("就绪")
        self.process_info = None


if __name__ == '__main__':
    root = tk.Tk()
    app = PortKillerGUI(root)
    root.mainloop()
