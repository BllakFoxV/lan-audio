# LAN Audio

**Stream âm thanh Windows tới điện thoại qua mạng LAN.**

[![Release](https://img.shields.io/github/v/release/BllakFoxV/lan-audio)](https://github.com/BllakFoxV/lan-audio/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-0078D4)](https://github.com/BllakFoxV/lan-audio/releases/latest)

LAN Audio thu âm thanh đang phát trên PC bằng WASAPI loopback và truyền trực tiếp
tới trình duyệt trên điện thoại. Không cần cài ứng dụng điện thoại, driver âm thanh
ảo hay Python khi dùng bản portable.

## Tải về

| Gói | Nội dung |
| --- | --- |
| [LAN Audio 0.1 — EXE](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/LAN-Audio-v0.1-Windows-x64.exe) | Một file chạy độc lập, đã kèm Python, QR và ADB |
| [LAN Audio 0.1 — ZIP](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/LAN-Audio-v0.1-Windows-x64.zip) | Giải nén rồi chạy `LAN Audio.exe` |
| [SHA256SUMS.txt](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/SHA256SUMS.txt) | Mã kiểm tra tính toàn vẹn của EXE và ZIP |

Yêu cầu: **Windows 10/11 64-bit**, thiết bị đầu ra âm thanh hoạt động và điện thoại
có Chrome/Safari hỗ trợ Web Audio. PC và điện thoại cần truy cập được nhau trong LAN.

## Sử dụng

1. Mở app — server tự khởi động, không có nút Bắt đầu/Dừng.
2. Nếu Windows hỏi quyền mạng, cho phép LAN Audio trên mạng Private đang dùng.
3. Quét QR bằng điện thoại, mở đường link rồi bấm **Bật nghe**.
4. Phát nhạc hoặc video trên PC. Đóng cửa sổ app để tắt server và thu âm.

PC có thể dùng Ethernet, điện thoại dùng Wi-Fi. Nếu PC có nhiều IP, chọn địa chỉ
cùng mạng với điện thoại trong danh sách tự hiện dưới QR. **Sao chép link** cho phép
mở client thủ công. Trên điện thoại có nút nghe/dừng và thanh âm lượng.

### Tự mở qua ADB

Nếu chưa có ai nghe và phát hiện thiết bị ADB đã cấp quyền (`device`), app mở link
trên trình duyệt mặc định của thiết bị. App kiểm tra thiết bị mỗi 3 giây.

- **Mỗi thiết bị chỉ được gọi mở link một lần trong suốt lần mở app.**
- Không mở lặp khi chưa bấm nghe, đổi IP, rút/cắm lại thiết bị hoặc khi lệnh lỗi.
- Đóng rồi mở lại app mới đặt lại giới hạn; thiết bị cắm vào sau cũng được phát hiện.
- Bỏ qua thiết bị `offline` / `unauthorized`; không tự cấp quyền USB debugging.

Bản portable có sẵn ADB. Điện thoại vẫn cần truy cập được link LAN và bấm
**Bật nghe** để đáp ứng quy tắc phát âm thanh của trình duyệt.

## Cách hoạt động

```text
Âm thanh Windows → WASAPI loopback → HTTP/PCM trong LAN → Web Audio trên điện thoại
                                      ↑
                              QR hoặc link qua ADB
```

- Thu thiết bị phát mặc định của Windows; **không thu microphone**.
- Truyền PCM float32; giữ sample rate của đầu ra, tối đa hai kênh.
- 48 kHz stereo sử dụng khoảng 3.1 Mbps cho mỗi thiết bị nghe.
- Buffer trình duyệt khoảng 120 ms; độ trễ thực tế phụ thuộc mạng và thiết bị.
- Token được tạo mới mỗi lần chạy. Cookie phiên giữ kết nối sau khi quét QR.
- Link thiếu/sai token vẫn mở trang hướng dẫn; luồng âm thanh yêu cầu token hợp lệ.

HTTP không mã hóa; dùng trong **LAN tin cậy**. Người có link/QR có thể nghe trong
lần chạy đó. Không mở cổng trực tiếp ra Internet.

## Mã nguồn và build

```text
app/                 GUI, server, web player, WASAPI và thư viện QR offline
build/               Script đóng gói, PyInstaller spec, phiên bản và release notes
tests/               Kiểm thử giao thức, xác thực, vòng đời server và ADB
.build/              Cache và binary thu âm đã biên dịch — không commit
.build-venv/         Môi trường build riêng — không commit
dist/                App portable, ZIP và checksum — không commit
CHANGELOG.md         Lịch sử phát hành
```

### Chạy từ mã nguồn

Cần Python có Tcl/Tk và .NET Framework C# compiler đi kèm Windows.
Thư viện QR đã được đóng gói trong `app/vendor/`, không cần pip khi chạy nguồn.

```powershell
python app/gui.py
# Hoặc nhấp đúp start.cmd / LAN Audio.vbs

# Đổi cổng hoặc chỉ định adapter:
python app/gui.py --port 8765 --bind 192.168.1.10

# Chế độ dòng lệnh; Ctrl+C để thoát:
python app/server.py --port 8765
```

Khi chạy từ nguồn, ADB là tùy chọn: đặt trong PATH, cạnh `app/gui.py`, hoặc trong
`platform-tools` của `ANDROID_SDK_ROOT` / `ANDROID_HOME`.

### Build portable

Đã build và kiểm thử với Python 3.15 x64. Cần Android platform-tools để đóng gói ADB.
Chạy từ thư mục gốc của repo:

```powershell
./build/build.ps1 -AdbDirectory C:/Soft/adb
```

Script tạo môi trường riêng, cài dependency theo `build/requirements-build.txt`,
chạy kiểm thử, biên dịch WASAPI helper và tạo EXE/ZIP/checksum trong `dist/`.

### Kiểm thử

```powershell
python -m unittest discover -s tests -t . -q
```

Bộ kiểm thử bao phủ xác thực QR/cookie, stream PCM, token mới khi khởi động lại,
cổng bị chiếm, dọn tiến trình thu âm và giới hạn ADB một lần cho mỗi thiết bị.

## Xử lý sự cố

| Triệu chứng | Cách xử lý |
| --- | --- |
| Điện thoại không mở được link | Kiểm tra cùng LAN, IP đã chọn, quyền Firewall và Wi-Fi guest/client isolation |
| Link hết hạn / yêu cầu ghép nối | Quét QR hiện tại; mỗi lần mở lại app sẽ có token mới |
| Cổng đang dùng | Đóng app/server cũ hoặc chạy với `--port` khác |
| Có kết nối nhưng không nghe | Bấm Bật nghe, kiểm tra âm lượng và thiết bị phát mặc định trên PC |
| Đổi loa / tai nghe | Đóng rồi mở lại app, quét QR mới |
| ADB không tự mở | Kiểm tra quyền USB debugging; giới hạn một lần được đặt lại khi mở lại app |

Nhật ký bản portable: `%LOCALAPPDATA%/LAN Audio/app.log`.

## Giới hạn

- Giữ trang web mở khi nghe; trình duyệt có thể dừng âm thanh khi khóa màn hình hoặc chạy nền.
- Âm thanh được bảo vệ hoặc ứng dụng dùng thiết bị ở chế độ exclusive có thể không thu được.
- Với đầu ra nhiều hơn hai kênh, chỉ truyền hai kênh đầu.
- Không tự kết nối lại sau khi đổi thiết bị âm thanh hoặc đổi mạng; mở lại app để làm mới.

## Thành phần bên thứ ba

QR sử dụng [python-qrcode](https://github.com/lincolnloop/python-qrcode) 8.2 (BSD-3-Clause).
Bản portable kèm Python, Tcl/Tk và Android platform-tools; các thông báo giấy phép
được đóng gói trong thư mục `licenses/` bên trong app.

Xem [CHANGELOG](CHANGELOG.md) và [các bản phát hành](https://github.com/BllakFoxV/lan-audio/releases).
