"""Stream the default Windows playback device to LAN browsers, with stdlib only."""
import argparse
import hmac
from http.cookies import SimpleCookie, CookieError
import http.server
import ipaddress
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import struct
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def read_exact(pipe, size):
    data = bytearray()
    while len(data) < size:
        part = pipe.read(size - len(data))
        if not part:
            raise EOFError("Windows audio capture stopped. Restart after changing the output device.")
        data.extend(part)
    return bytes(data)


def build_capture():
    source, binary = ROOT / "Loopback.cs", ROOT / "Loopback.exe"
    if getattr(sys, "frozen", False):
        if not binary.exists():
            raise RuntimeError("Bundled Windows audio capture executable is missing.")
    elif not binary.exists() or source.stat().st_mtime > binary.stat().st_mtime:
        compiler = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        if not compiler.exists():
            raise RuntimeError("Windows .NET Framework C# compiler not found.")
        subprocess.run([str(compiler), "/nologo", "/optimize+", "/platform:x64", f"/out:{binary}", str(source)],
                       check=True, capture_output=True, creationflags=NO_WINDOW)
    return subprocess.Popen([str(binary)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=NO_WINDOW)


def lan_addresses():
    addresses = set()
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "Get-NetIPAddress -AddressFamily IPv4 | Select-Object -ExpandProperty IPAddress"],
            capture_output=True, text=True, timeout=10, creationflags=NO_WINDOW)
        candidates = result.stdout.split()
    except (OSError, subprocess.TimeoutExpired):
        try:
            candidates = socket.gethostbyname_ex(socket.gethostname())[2]
        except OSError:
            candidates = []
    for candidate in candidates:
        try:
            address = ipaddress.ip_address(candidate)
            if not address.is_loopback and not address.is_link_local:
                addresses.add(str(address))
        except ValueError:
            pass
    preferred = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            # Route lookup only; no packet is sent.
            probe.connect(("192.0.2.1", 9))
            preferred = probe.getsockname()[0]
    except OSError:
        pass
    return sorted(addresses, key=lambda address: (address != preferred, address))


class AudioHub:
    def __init__(self, process):
        self.process = process
        self.header = read_exact(process.stdout, 12)
        magic, self.rate, self.channels = struct.unpack("<4sII", self.header)
        if magic != b"LAN1" or not 8000 <= self.rate <= 384000 or self.channels not in (1, 2):
            raise ValueError("Invalid capture header")
        self.clients = set()
        self.lock = threading.Lock()
        self.error = None
        self.stopping = threading.Event()

    def pump(self):
        try:
            while True:
                prefix = read_exact(self.process.stdout, 4)
                size, = struct.unpack("<I", prefix)
                if not 0 < size <= self.rate * self.channels * 4:
                    raise ValueError("Invalid audio packet")
                packet = prefix + read_exact(self.process.stdout, size)
                with self.lock:
                    for client in self.clients:
                        if client.full():
                            try:
                                client.get_nowait()  # Consumers may have drained it meanwhile.
                            except queue.Empty:
                                pass
                        client.put_nowait(packet)
        except (EOFError, OSError, ValueError) as exc:
            if not self.stopping.is_set():
                self.error = str(exc)


def make_handler(hub, token):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not write access tokens to logs.

        def do_GET(self):
            url = urlsplit(self.path)
            supplied = parse_qs(url.query, keep_blank_values=True).get("token", [None])[0]
            if supplied is None:
                cookie = SimpleCookie()
                try:
                    cookie.load(self.headers.get("Cookie", ""))
                except CookieError:
                    pass
                saved = cookie.get("lan_audio")
                supplied = saved.value if saved else ""
            authenticated = hmac.compare_digest(supplied.encode(), token.encode())
            # Always serve the shell, including for missing/expired QR links.
            if url.path == "/":
                self.reply((ROOT / "player.html").read_bytes(), "text/html; charset=utf-8",
                           session=authenticated)
                return
            if url.path == "/favicon.ico":
                self.reply(b"", "image/x-icon")
                return
            if not authenticated:
                self.reply(json.dumps({"error": "pairing_required"}).encode(),
                           "application/json", status=403)
                return
            if url.path == "/status":
                self.reply(json.dumps({"rate": hub.rate, "channels": hub.channels,
                                       "error": hub.error}).encode(), "application/json")
            elif url.path == "/stream":
                if hub.error:
                    self.send_error(503, hub.error)
                    return
                client = queue.Queue(maxsize=20)
                with hub.lock:
                    hub.clients.add(client)
                try:
                    self.connection.settimeout(10)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(hub.header)
                    self.wfile.flush()
                    while not hub.error and not hub.stopping.is_set():
                        try:
                            packet = client.get(timeout=1)
                        except queue.Empty:
                            # Zero length is a keepalive, not an audio packet.
                            packet = b"\0\0\0\0"
                        self.wfile.write(packet)
                        self.wfile.flush()
                except (OSError, TimeoutError):
                    pass
                finally:
                    with hub.lock:
                        hub.clients.discard(client)
            else:
                self.send_error(404)

        def reply(self, data, content_type, status=200, session=False):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            if session:
                self.send_header("Set-Cookie", f"lan_audio={token}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()
            self.wfile.write(data)
    return Handler


class AudioService:
    """Reusable capture/server lifecycle, shared by the GUI and CLI."""

    def __init__(self):
        self.process = self.hub = self.server = None
        self.server_thread = self.pump_thread = self.stderr_thread = None
        self.token = None
        self.diagnostics = []

    def start(self, bind="0.0.0.0", port=8765):
        if self.process is not None:
            raise RuntimeError("Server is already running")
        if not 0 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        self.diagnostics = []
        try:
            # Bind first so a busy port never starts a capture process.
            self.token = secrets.token_urlsafe(18)
            self.server = http.server.ThreadingHTTPServer((bind, port), make_handler(None, self.token))
            self.server.daemon_threads = True
            self.process = build_capture()
            process = self.process

            def drain_stderr():
                for line in iter(process.stderr.readline, b""):
                    self.diagnostics.append(line.decode("utf-8", errors="replace").strip())
                    del self.diagnostics[:-20]

            self.stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
            self.stderr_thread.start()
            result = queue.Queue()

            def read_header():
                try:
                    result.put(AudioHub(process))
                except Exception as exc:
                    result.put(exc)

            header_thread = threading.Thread(target=read_header, daemon=True)
            header_thread.start()
            try:
                hub = result.get(timeout=12)
            except queue.Empty:
                raise RuntimeError("Windows audio capture did not start within 12 seconds.") from None
            if isinstance(hub, Exception):
                if self.stderr_thread:
                    self.stderr_thread.join(timeout=0.5)
                raise RuntimeError("\n".join(self.diagnostics) or str(hub))
            self.hub = hub
            self.server.RequestHandlerClass = make_handler(hub, self.token)
            self.pump_thread = threading.Thread(target=hub.pump, daemon=True)
            self.server_thread = threading.Thread(target=self.server.serve_forever,
                                                  kwargs={"poll_interval": 0.1}, daemon=True)
            self.pump_thread.start()
            self.server_thread.start()
            return self
        except Exception:
            self.stop()
            raise

    @property
    def port(self):
        return self.server.server_address[1] if self.server else None

    @property
    def client_count(self):
        if not self.hub:
            return 0
        with self.hub.lock:
            return len(self.hub.clients)

    def url(self, address):
        return f"http://{address}:{self.port}/?token={self.token}"

    def stop(self):
        if self.hub:
            self.hub.stopping.set()
        if self.server:
            if self.server_thread and self.server_thread.is_alive():
                self.server.shutdown()
                self.server_thread.join(timeout=3)
            self.server.server_close()
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=3)
            if self.pump_thread:
                self.pump_thread.join(timeout=2)
            if self.stderr_thread:
                self.stderr_thread.join(timeout=2)
            self.process.stdout.close()
            self.process.stderr.close()
        self.process = self.hub = self.server = None
        self.server_thread = self.pump_thread = self.stderr_thread = None
        self.token = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    service = AudioService()
    try:
        service.start(args.bind, args.port)
        print("\nLAN Audio is ready. Open ONE of these links on your phone:", flush=True)
        addresses = lan_addresses() if args.bind == "0.0.0.0" else [args.bind]
        for address in addresses:
            print(f"  {service.url(address)}", flush=True)
        print(f"PC test: {service.url('127.0.0.1')}", flush=True)
        print("Same LAN required. Allow Python on your trusted private network if Windows asks.", flush=True)
        print("Press Ctrl+C to stop. Restart after changing the Windows output device.\n", flush=True)
        while not service.hub.error:
            threading.Event().wait(0.25)
        raise RuntimeError(service.hub.error)
    except KeyboardInterrupt:
        print("\nStopped.")
    except (OSError, RuntimeError, ValueError, EOFError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    finally:
        service.stop()


if __name__ == "__main__":
    main()
