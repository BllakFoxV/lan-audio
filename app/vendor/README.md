# Offline QR dependency

`qrcode-8.2-py3-none-any.whl` is the unmodified python-qrcode 8.2 wheel from PyPI.
The application imports it directly as a ZIP; no pip installation, Pillow, or
internet connection is needed at launch. Tk renders the QR matrix locally.

Upstream: https://github.com/lincolnloop/python-qrcode
License: BSD-3-Clause, included inside the wheel at `qrcode-8.2.dist-info/LICENSE`.

To obtain the same dependency again:

```powershell
python -m pip download --no-deps --dest vendor qrcode==8.2
```
