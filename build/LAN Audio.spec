# Build from the project root using build/build.ps1.
from importlib.metadata import distribution
from pathlib import Path
import os
import shutil
import sys

root = Path(SPECPATH).parent
source = root / "app"
adb_dir = os.environ.get("LAN_AUDIO_ADB_DIR")
adb = Path(adb_dir) / "adb.exe" if adb_dir else Path(shutil.which("adb") or "adb.exe")
if not adb.is_file():
    raise RuntimeError("Set LAN_AUDIO_ADB_DIR to the Android platform-tools directory.")

binaries = [(str(root / ".build" / "capture" / "Loopback.exe"), ".")]
for name in ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "libwinpthread-1.dll"):
    candidate = adb.parent / name
    if candidate.is_file():
        binaries.append((str(candidate), "adb"))

datas = [(str(source / "player.html"), ".")]
notice = adb.parent / "NOTICE.txt"
if not notice.is_file():
    raise RuntimeError("Android platform-tools NOTICE.txt is required for distribution.")
datas.append((str(notice), "licenses/android-platform-tools"))
qr = distribution("qrcode")
for file in qr.files:
    if file.name == "LICENSE":
        datas.append((str(qr.locate_file(file)), "licenses/python-qrcode"))
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.is_file():
    datas.append((str(python_license), "licenses/python"))

a = Analysis(
    [str(source / "gui.py")],
    pathex=[str(source)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["unittest", "pytest", "PIL"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="LAN Audio",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version=str(root / "build" / "version_info.txt"),
)
