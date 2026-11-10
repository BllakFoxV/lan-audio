# LAN Audio

Nghe âm thanh từ máy tính Windows trên điện thoại qua mạng LAN.
Ứng dụng lấy âm thanh từ thiết bị phát mặc định của Windows bằng WASAPI loopback
và truyền đến trình duyệt trên điện thoại.

## Tải về

Tải bản [LAN Audio 0.1](https://github.com/BllakFoxV/lan-audio/releases/tag/v0.1):

| File | Cách dùng |
| --- | --- |
| [EXE](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/LAN-Audio-v0.1-Windows-x64.exe) | Tải về và mở trực tiếp |
| [ZIP](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/LAN-Audio-v0.1-Windows-x64.zip) | Giải nén rồi mở `LAN Audio.exe` |
| [SHA256SUMS.txt](https://github.com/BllakFoxV/lan-audio/releases/download/v0.1/SHA256SUMS.txt) | Mã SHA-256 để kiểm tra file EXE và ZIP |

Bản đóng gói đã kèm Python, thư viện tạo QR, chương trình thu âm và ADB.

## Yêu cầu

- Máy tính chạy Windows 10/11 64-bit và có thiết bị phát âm thanh hoạt động.
- Điện thoại dùng trình duyệt Chrome hoặc Safari phiên bản mới, hỗ trợ Web Audio.
- Máy tính và điện thoại truy cập được nhau qua mạng LAN. Máy tính có thể dùng
  dây mạng, điện thoại dùng Wi-Fi.

## Cách dùng

1. Mở LAN Audio. Ứng dụng tự bắt đầu chia sẻ âm thanh.
2. Cho phép truy cập mạng Private nếu Windows Firewall hỏi.
3. Quét QR bằng điện thoại, mở link và bấm **Bật nghe**.
4. Phát nhạc hoặc video trên máy tính để nghe trên điện thoại.
5. Đóng cửa sổ LAN Audio khi muốn kết thúc chia sẻ.

Nếu máy tính có nhiều địa chỉ IP, chọn IP cùng mạng với điện thoại ở danh sách
dưới QR. Có thể bấm **Sao chép link** để mở link thủ công.
Trang nghe trên điện thoại có nút **Bật nghe / Dừng nghe** và thanh chỉnh âm lượng.

### Mở link bằng ADB

Khi chưa có thiết bị nào đang nghe, ứng dụng có thể tự mở link trên thiết bị
Android được ADB nhận diện ở trạng thái `device`. Thiết bị cần bật USB debugging
và cấp quyền kết nối ADB cho máy tính.

Mỗi thiết bị được thử mở link một lần trong mỗi lần chạy ứng dụng, kể cả khi
lệnh mở thất bại. Điện thoại vẫn cần truy cập được mạng LAN và bấm **Bật nghe**.

## Lưu ý

- Link có token truy cập riêng cho mỗi lần chạy. Mở lại ứng dụng thì quét QR mới.
- Kết nối dùng HTTP, không mã hóa. Chỉ dùng trong LAN tin cậy và giữ kín link/QR.
- Giữ trang nghe mở. Trình duyệt có thể tạm dừng âm thanh khi khóa màn hình
  hoặc chạy nền.
- Khi đổi thiết bị phát âm thanh hoặc đổi mạng, mở lại ứng dụng và quét QR mới.
- Âm thanh truyền ở dạng PCM float32, tối đa hai kênh. Với thiết bị nhiều kênh,
  ứng dụng lấy hai kênh đầu.
- Độ trễ phụ thuộc mạng và thiết bị. Nội dung được bảo vệ hoặc thiết bị phát
  ở chế độ exclusive có thể không thu được.

## Xử lý lỗi thường gặp

| Vấn đề | Cách kiểm tra |
| --- | --- |
| Điện thoại không mở được link | Kiểm tra mạng LAN, IP đã chọn và quyền Windows Firewall. Wi-Fi khách có thể chặn kết nối giữa các thiết bị. |
| Link hết hạn | Quét lại QR đang hiển thị trên máy tính. |
| Đã kết nối nhưng không có tiếng | Bấm **Bật nghe**, kiểm tra âm lượng trên điện thoại và thiết bị phát mặc định của Windows. |
| Cổng đang được dùng | Đóng phiên LAN Audio cũ hoặc chạy từ dòng lệnh với `--port` khác. |
| ADB không mở link | Kiểm tra thiết bị bằng `adb devices` và cấp quyền USB debugging. Mở lại ứng dụng để thử lại. |

Nhật ký của bản đóng gói nằm tại `%LOCALAPPDATA%\LAN Audio\app.log`.

## Chạy từ mã nguồn

Cần Python 3 64-bit có Tcl/Tk và trình biên dịch C# của .NET Framework tại
`%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe`.
Thư viện QR đã có trong `app/vendor/`.

Chạy các lệnh sau từ thư mục gốc của dự án:

```powershell
python app/gui.py
```

Cũng có thể mở `start.cmd` hoặc `LAN Audio.vbs` khi Python đã có trong PATH.

```powershell
# Chọn cổng và địa chỉ mạng của máy tính
python app/gui.py --port 8765 --bind 192.168.1.10

# Chạy server trong terminal, nhấn Ctrl+C để dừng
python app/server.py --port 8765
```

Để dùng ADB khi chạy từ nguồn, thêm ADB vào PATH, đặt cạnh `app/gui.py`, hoặc đặt
trong thư mục `platform-tools` của `ANDROID_SDK_ROOT` / `ANDROID_HOME`.

## Build và kiểm thử

Để tạo bản đóng gói, chuẩn bị Android platform-tools có `adb.exe` và `NOTICE.txt`,
rồi chạy:

```powershell
./build/build.ps1 -AdbDirectory C:/Soft/adb
```

Thay `C:/Soft/adb` bằng thư mục platform-tools trên máy.
Script cài thư viện build trong `.build-venv/`, biên dịch phần thu âm, chạy kiểm thử
và tạo EXE, ZIP, checksum trong `dist/`.

Chạy riêng bộ kiểm thử:

```powershell
python -m unittest discover -s tests -t . -q
```

Mã ứng dụng nằm trong `app/`, cấu hình đóng gói trong `build/` và kiểm thử trong `tests/`.

## Thư viện và công cụ sử dụng

- [python-qrcode](https://github.com/lincolnloop/python-qrcode) 8.2, giấy phép BSD-3-Clause.
- Python và Tcl/Tk cho ứng dụng desktop.
- Android platform-tools để mở link qua ADB.

Xem lịch sử phát hành trong [CHANGELOG.md](CHANGELOG.md).
