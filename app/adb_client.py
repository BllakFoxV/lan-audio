"""Open the paired LAN player on authorized Android devices, without blocking Tk."""
import os
import logging
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading

NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def find_adb():
    if getattr(sys, "frozen", False):
        bundled = Path(__file__).resolve().parent / "adb" / "adb.exe"
        if bundled.is_file():
            return str(bundled)
        # Also support placing a custom adb.exe beside the portable app.
        external = Path(sys.executable).resolve().parent / "adb.exe"
        if external.is_file():
            return str(external)
    executable = shutil.which("adb")
    if executable:
        return executable
    roots = [Path(__file__).resolve().parent]
    for name in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        if os.environ.get(name):
            roots.append(Path(os.environ[name]) / "platform-tools")
    for root in roots:
        candidate = root / ("adb.exe" if os.name == "nt" else "adb")
        if candidate.is_file():
            return str(candidate)
    return None


class AdbAutoOpen:
    def __init__(self, can_open, notify=lambda message: None, attempted=None):
        self.can_open = can_open
        self.notify = notify
        self.url = ""
        self.cancelled = threading.Event()
        # Shared across sharing sessions; only closing the app resets this set.
        self.attempted = attempted if attempted is not None else set()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def cancel(self):
        self.cancelled.set()

    def wait(self):
        if self.thread.ident is not None:
            self.thread.join(timeout=8)

    def command(self, executable, *args):
        return subprocess.run([executable, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=5,
                              creationflags=NO_WINDOW)

    def eligible(self, url):
        return bool(url) and not self.cancelled.is_set() and self.url == url and self.can_open()

    def poll(self):
        url = self.url
        if not self.eligible(url):
            return
        executable = find_adb()
        if not executable:
            return  # ADB is optional; QR pairing still works.
        try:
            result = self.command(executable, "devices")
        except (OSError, subprocess.TimeoutExpired):
            return
        if result.returncode:
            return
        for line in result.stdout.splitlines():
            columns = line.split()
            if len(columns) != 2 or columns[1] != "device":
                continue  # Never act on unauthorized/offline devices.
            serial = columns[0]
            if serial in self.attempted:
                continue
            if not self.eligible(url):
                return
            # Count the attempt, including errors/timeouts: never repeatedly
            # open a browser while the user hasn't connected or tapped Play.
            self.attempted.add(serial)
            try:
                # adb forwards shell arguments to Android's POSIX shell.
                result = self.command(executable, "-s", serial, "shell", "am", "start",
                                      "-a", "android.intent.action.VIEW", "-d", shlex.quote(url))
                output = result.stdout + result.stderr
                success = result.returncode == 0 and "Error:" not in output and "Exception" not in output
            except (OSError, subprocess.TimeoutExpired):
                success = False
            if success:
                logging.info("Opened player on an ADB device")
                if self.eligible(url):
                    self.notify("Đã mở link qua ADB · Bấm Bật nghe trên điện thoại")
            else:
                logging.warning("ADB browser launch failed; automatic retry suppressed")

    def run(self):
        while not self.cancelled.is_set():
            self.poll()
            self.cancelled.wait(3)
