import subprocess
import unittest
from unittest.mock import Mock, patch

from adb_client import AdbAutoOpen


class AdbTests(unittest.TestCase):
    def setUp(self):
        self.connected = False
        self.devices = "List of devices attached\nphone1\tdevice\n"
        self.on_discovery = lambda: None
        self.launch_error = None
        self.notify = Mock()
        self.monitor = AdbAutoOpen(lambda: not self.connected, self.notify)
        self.monitor.url = "http://192.168.1.10:8765/?token=test"
        self.command = Mock(side_effect=self.fake_command)
        self.monitor.command = self.command
        finder = patch("adb_client.find_adb", return_value="adb")
        finder.start()
        self.addCleanup(finder.stop)

    def fake_command(self, executable, *args):
        if args == ("devices",):
            self.on_discovery()
            return subprocess.CompletedProcess([], 0, self.devices, "")
        if self.launch_error:
            raise self.launch_error
        return subprocess.CompletedProcess([], 0, "Starting: Intent { ... }", "")

    def launches(self):
        return [call for call in self.command.call_args_list if "am" in call.args]

    def test_only_authorized_devices_and_once_even_without_playback(self):
        self.devices += "phone2\tunauthorized\nphone3\toffline\nphone4\tdevice\n"
        for _ in range(10):
            self.monitor.poll()
        self.assertEqual(len(self.launches()), 2)
        self.assertEqual(self.monitor.attempted, {"phone1", "phone4"})
        args = self.launches()[0].args
        self.assertIn("phone1", args)
        self.assertIn("android.intent.action.VIEW", args)
        self.assertEqual(args[-1], "'" + self.monitor.url + "'")

    def test_no_launch_while_any_listener_connected(self):
        self.connected = True
        self.monitor.poll()
        self.command.assert_not_called()
        self.connected = False
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 1)

    def test_changed_url_and_restarted_sharing_do_not_reopen(self):
        self.monitor.poll()
        self.monitor.url = "http://192.168.1.11:8765/?token=new"
        self.monitor.poll()
        next_session = AdbAutoOpen(lambda: True, attempted=self.monitor.attempted)
        next_session.url = self.monitor.url
        next_session.command = self.command
        next_session.poll()
        self.assertEqual(len(self.launches()), 1)
        fresh_app = AdbAutoOpen(lambda: True)
        fresh_app.url = self.monitor.url
        fresh_app.command = self.command
        fresh_app.poll()
        self.assertEqual(len(self.launches()), 2)

    def test_failed_or_timed_out_launch_is_never_retried(self):
        self.launch_error = subprocess.TimeoutExpired("adb", 5)
        self.monitor.poll()
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 1)
        self.notify.assert_not_called()

    def test_new_device_and_later_authorization_are_detected(self):
        self.devices = "List of devices attached\nphone1\tunauthorized\n"
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 0)
        self.devices = "List of devices attached\nphone1\tdevice\nphone2\tdevice\n"
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 2)

    def test_disconnect_reconnect_does_not_reset_limit(self):
        self.monitor.poll()
        self.devices = "List of devices attached\n"
        self.monitor.poll()
        self.devices += "phone1\tdevice\n"
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 1)

    def test_stop_or_connection_during_discovery_prevents_open(self):
        self.on_discovery = self.monitor.cancel
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 0)
        self.assertFalse(self.monitor.attempted)

    def test_listener_appearing_during_discovery_prevents_open(self):
        self.on_discovery = lambda: setattr(self, "connected", True)
        self.monitor.poll()
        self.assertEqual(len(self.launches()), 0)

    def test_no_adb_or_no_url_keeps_qr_flow(self):
        with patch("adb_client.find_adb", return_value=None):
            self.monitor.poll()
        self.monitor.url = ""
        self.monitor.poll()
        self.command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
