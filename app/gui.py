"""LAN Audio desktop controls. QR generation works offline with the bundled wheel."""
import argparse
import ctypes
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from server import AudioService, lan_addresses
from adb_client import AdbAutoOpen

ROOT = Path(__file__).resolve().parent
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(ROOT / "vendor" / "qrcode-8.2-py3-none-any.whl"))
import qrcode

BG = "#101822"
TEXT = "#f1f6fc"
MUTED = "#aebed0"


def qr_image(master, url):
    code = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_M, border=4)
    code.add_data(url)
    code.make(fit=True)
    matrix = code.get_matrix()
    image = tk.PhotoImage(master=master, width=len(matrix), height=len(matrix))
    image.put(" ".join("{" + " ".join("#000000" if cell else "#ffffff" for cell in row) + "}"
                       for row in matrix))
    return image.zoom(max(1, 256 // len(matrix)))


class App:
    def __init__(self, root, port=8765, bind="0.0.0.0"):
        self.root = root
        self.service = AudioService()
        self.events = queue.Queue()
        self.state = "stopped"
        self.closing = False
        self.adb_monitor = None
        self.adb_attempted = set()
        self.bind = bind
        self.addresses = []
        self.qr = None
        self.port = tk.StringVar(value=str(port))
        self.address = tk.StringVar()
        self.link = tk.StringVar()
        self.status = tk.StringVar(value="Đang khởi động…")
        self.hint = tk.StringVar(value="Cùng Wi-Fi / LAN · Quét QR để nghe")
        root.title("LAN Audio")
        root.configure(bg=BG)
        root.geometry("370x470")
        root.minsize(350, 450)
        root.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TCombobox", padding=7, font=("Segoe UI", 11))
        self.build_ui()
        root.after(0, self.start_service)
        root.after(100, self.tick)

    def label(self, parent, text=None, variable=None, size=11, color=TEXT, **kw):
        return tk.Label(parent, text=text, textvariable=variable, bg=parent["bg"], fg=color,
                        font=("Segoe UI", size), anchor="w", **kw)

    def build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=24, pady=18)
        outer.pack(fill="both", expand=True)
        self.label(outer, "LAN Audio", size=18).pack()
        self.label(outer, variable=self.status, size=10, color=MUTED).pack(pady=(3, 12))
        frame = tk.Frame(outer, bg="white", width=256, height=256)
        frame.pack()
        frame.pack_propagate(False)
        self.qr_box = tk.Label(frame, text="Đang khởi động…", bg="white", fg="#536273",
                               font=("Segoe UI", 11))
        self.qr_box.pack(fill="both", expand=True)
        self.network = ttk.Combobox(outer, textvariable=self.address, state="readonly", width=23)
        self.network.bind("<<ComboboxSelected>>", lambda _: self.update_qr())
        self.copy = tk.Button(outer, text="Sao chép link", command=self.copy_link, bg=BG, fg=MUTED,
                              activebackground=BG, activeforeground=TEXT, relief="flat", bd=0,
                              font=("Segoe UI", 10), cursor="hand2", state="disabled")
        self.copy.pack(pady=(12, 0))
        self.label(outer, variable=self.hint, size=9, color=MUTED, wraplength=300,
                   justify="center").pack(pady=(6, 0))

    def refresh_addresses(self):
        def work():
            try:
                addresses = lan_addresses() if self.bind == "0.0.0.0" else [self.bind]
                self.events.put(("addresses", addresses))
            except Exception as exc:
                self.events.put(("network_error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def update_qr(self):
        ready = self.state == "running" and bool(self.address.get())
        self.copy.configure(state="normal" if ready else "disabled")
        if ready:
            url = self.service.url(self.address.get())
            self.link.set(url)
            self.qr = qr_image(self.root, url)
            self.qr_box.configure(image=self.qr, text="")
            logging.info("Player QR ready")
        else:
            self.link.set("")
            self.qr_box.configure(image="", text="Chưa có địa chỉ LAN" if self.state == "running"
                                  else "Đang khởi động…" if self.state == "starting"
                                  else "Đang đóng…" if self.closing else "Không hoạt động")
            self.qr = None
        if self.adb_monitor:
            self.adb_monitor.url = self.link.get()

    def start_service(self):
        if self.closing or self.state != "stopped":
            return
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cổng không hợp lệ", "Cổng phải từ 1 đến 65535.", parent=self.root)
            self.status.set("Không khởi động được")
            self.update_qr()
            return
        self.refresh_addresses()
        self.state = "starting"
        self.status.set("Đang khởi động…")
        def work():
            try:
                self.service.start(self.bind, port)
                self.events.put(("started", None))
            except Exception as exc:
                self.events.put(("start_error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def stop_service(self):
        monitor = self.adb_monitor
        self.adb_monitor = None
        if monitor:
            monitor.cancel()
        self.state = "stopping"
        self.status.set("Đang dừng…")
        self.update_qr()
        def work():
            try:
                if monitor:
                    monitor.wait()
                self.service.stop()
                self.events.put(("stopped", None))
            except Exception as exc:
                self.events.put(("stop_error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def copy_link(self):
        if self.link.get():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.link.get())
            self.hint.set("Đã sao chép link")

    def reset(self):
        self.state = "stopped"
        self.status.set("Không hoạt động")
        self.update_qr()

    def tick(self):
        while True:
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "addresses":
                self.addresses = value
                self.network.configure(values=value)
                if len(value) > 1:
                    self.network.pack(before=self.copy, pady=(8, 0))
                else:
                    self.network.pack_forget()
                if self.address.get() not in value:
                    self.address.set(value[0] if value else "")
                self.hint.set("Chọn IP cùng mạng với điện thoại" if len(value) > 1
                              else "Cùng Wi-Fi / LAN · Quét QR để nghe" if value
                              else "Chưa có mạng LAN. Kết nối rồi mở lại app.")
                self.update_qr()
            elif event == "network_error":
                self.hint.set("Không đọc được địa chỉ mạng: " + value)
            elif event == "started":
                self.state = "running"
                self.hint.set("Quét QR → mở link → Bật nghe")
                self.update_qr()
                if self.closing:
                    self.stop_service()
                else:
                    monitor = AdbAutoOpen(
                        lambda: self.state == "running" and self.service.client_count == 0
                        and self.service.hub is not None and not self.service.hub.error,
                        attempted=self.adb_attempted)
                    monitor.notify = lambda message, source=monitor: self.events.put(("adb_opened", (source, message)))
                    monitor.url = self.link.get()
                    self.adb_monitor = monitor
                    monitor.start()
            elif event == "adb_opened":
                monitor, message = value
                if monitor is self.adb_monitor and self.state == "running":
                    self.hint.set(message)
            elif event in ("stopped", "start_error", "stop_error"):
                self.reset()
                if event != "stopped" and not self.closing:
                    self.hint.set("Không khởi động được. Kiểm tra server cũ hoặc cổng đang dùng.")
                    messagebox.showerror("LAN Audio", value, parent=self.root)
        if self.closing and self.state == "stopped":
            self.root.destroy()
            return
        if self.state == "running":
            self.status.set(f"Đang chia sẻ · {self.service.client_count} đang nghe")
            if self.service.hub.error:
                error = self.service.hub.error
                self.stop_service()
                self.hint.set("Thu âm đã ngắt: " + error + " Mở lại app để kết nối lại.")
        self.root.after(200, self.tick)

    def close(self):
        self.closing = True
        if self.state == "running":
            self.stop_service()
        elif self.state == "stopped":
            self.root.destroy()
        else:
            self.status.set("Đang đóng…")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()
    if getattr(sys, "frozen", False):
        log_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LAN Audio"
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(
            log_dir / "app.log", maxBytes=256000, backupCount=1, encoding="utf-8")],
            format="%(asctime)s %(levelname)s %(message)s")
        logging.info("Starting LAN Audio portable")
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    if getattr(sys, "frozen", False):
        root.report_callback_exception = lambda kind, value, trace: logging.error(
            "GUI callback failed", exc_info=(kind, value, trace))
    App(root, args.port, args.bind)
    root.mainloop()


if __name__ == "__main__":
    main()
