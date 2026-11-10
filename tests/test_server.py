"""Protocol/lifecycle checks using an isolated fake capture process."""
import http.client
import socket
import struct
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from server import AudioService


def fake_capture():
    code = (
        "import struct,sys,time\n"
        "out=sys.stdout.buffer\n"
        "out.write(struct.pack('<4sII',b'LAN1',48000,2)); out.flush()\n"
        "while True:\n"
        " out.write(struct.pack('<Iff',8,0.25,-0.25)); out.flush(); time.sleep(0.01)\n"
    )
    return subprocess.Popen([sys.executable, "-u", "-c", code], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AudioService()
        self.capture = patch("server.build_capture", side_effect=fake_capture)
        self.capture.start()
        self.addCleanup(self.capture.stop)
        self.addCleanup(self.service.stop)

    def start(self):
        self.service.start("127.0.0.1", 0)
        return self.service.url("127.0.0.1")

    def test_page_status_and_token(self):
        url = self.start()
        with urlopen(url, timeout=3) as response:
            self.assertIn("Bật nghe".encode(), response.read())
            self.assertEqual(response.headers["Cache-Control"], "no-store")
        with urlopen(url.replace("/?", "/status?"), timeout=3) as response:
            self.assertIn(b'"rate": 48000', response.read())
        for path in ("/status", "/stream"):
            with self.assertRaises(HTTPError) as caught:
                urlopen(f"http://127.0.0.1:{self.service.port}{path}?token=wrong", timeout=3)
            self.assertEqual(caught.exception.code, 403)
            caught.exception.close()

    def test_stream_count_and_shutdown(self):
        self.start()
        connection = http.client.HTTPConnection("127.0.0.1", self.service.port, timeout=3)
        connection.request("GET", "/stream?token=" + self.service.token)
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(struct.unpack("<4sII", response.read(12)), (b"LAN1", 48000, 2))
        self.assertEqual(struct.unpack("<Iff", response.read(12)), (8, 0.25, -0.25))
        self.assertEqual(self.service.client_count, 1)
        process = self.service.process
        self.service.stop()
        self.assertIsNotNone(process.poll())
        response.close()
        connection.close()
        self.assertEqual(self.service.client_count, 0)

    def test_restart_changes_token_and_releases_port(self):
        self.start()
        old_token, port = self.service.token, self.service.port
        self.service.stop()
        self.service.start("127.0.0.1", port)
        self.assertNotEqual(self.service.token, old_token)
        with self.assertRaises(HTTPError) as caught:
            urlopen(f"http://127.0.0.1:{port}/status?token={old_token}", timeout=3)
        self.assertEqual(caught.exception.code, 403)
        caught.exception.close()

    def test_unpaired_and_expired_links_open_player_without_granting_audio(self):
        self.start()
        base = f"http://127.0.0.1:{self.service.port}"
        for path in ("/", "/?token=expired"):
            with urlopen(base + path, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"pairingMessage", response.read())
                self.assertIsNone(response.headers.get("Set-Cookie"))

    def test_qr_sets_cookie_and_reopening_without_query_keeps_pairing(self):
        self.start()
        conn = http.client.HTTPConnection("127.0.0.1", self.service.port, timeout=3)
        self.addCleanup(conn.close)
        conn.request("GET", "/?token=" + self.service.token)
        response = conn.getresponse()
        cookie = response.getheader("Set-Cookie")
        response.read()
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        headers = {"Cookie": cookie.split(";", 1)[0]}
        conn.request("GET", "/status", headers=headers)
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        response.read()
        conn.request("GET", "/stream", headers=headers)
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(4), b"LAN1")
        response.close()
        conn.close()
        conn.request("GET", "/status?token=wrong", headers=headers)
        response = conn.getresponse()
        self.assertEqual(response.status, 403)
        self.assertIn(b"pairing_required", response.read())

    def test_busy_port_does_not_start_capture(self):
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen()
            with self.assertRaises(OSError):
                self.service.start("127.0.0.1", occupied.getsockname()[1])
        self.assertIsNone(self.service.process)

    def test_capture_failure_cleans_up_and_can_retry(self):
        def failed_capture():
            return subprocess.Popen([sys.executable, "-c", "import sys; sys.stderr.write('capture failed')"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with patch("server.build_capture", side_effect=failed_capture):
            with self.assertRaisesRegex(RuntimeError, "capture failed"):
                self.start()
        self.assertIsNone(self.service.process)
        self.assertIsNone(self.service.server)
        self.start()
        self.service.process.terminate()
        deadline = time.monotonic() + 3
        while not self.service.hub.error and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertIsNotNone(self.service.hub.error)


if __name__ == "__main__":
    unittest.main()
