## LAN Audio 0.1

Bản phát hành đầu tiên. Nghe âm thanh từ máy tính Windows trên trình duyệt
điện thoại qua mạng LAN.

### Tính năng

- Tự bắt đầu chia sẻ âm thanh khi mở ứng dụng.
- Quét QR hoặc sao chép link để kết nối điện thoại.
- Chọn IP khi máy tính có nhiều địa chỉ mạng.
- Bật/dừng nghe, chỉnh âm lượng và xem trạng thái trên điện thoại.
- Tự mở link trên thiết bị Android đã cấp quyền ADB khi chưa có ai nghe.
  Mỗi thiết bị được thử mở một lần trong mỗi lần chạy ứng dụng.

### Tải và chạy

1. Tải `LAN-Audio-v0.1-Windows-x64.exe` và mở trực tiếp, hoặc giải nén file ZIP
   rồi mở `LAN Audio.exe`.
2. Cho phép truy cập mạng Private nếu Windows Firewall hỏi.
3. Quét QR bằng điện thoại, mở link và bấm **Bật nghe**.
4. Phát âm thanh trên máy tính. Đóng ứng dụng để kết thúc chia sẻ.

Bản đóng gói đã kèm Python, thư viện tạo QR, chương trình thu âm và ADB.
File `SHA256SUMS.txt` chứa mã SHA-256 của EXE và ZIP.

### Yêu cầu và lưu ý

- Windows 10/11 64-bit, có thiết bị phát âm thanh hoạt động.
- Điện thoại có Chrome hoặc Safari phiên bản mới và truy cập được máy tính qua LAN.
- Dùng trong LAN tin cậy vì kết nối HTTP không mã hóa. Giữ kín link/QR.
- Giữ trang nghe mở; trình duyệt có thể dừng âm thanh khi khóa màn hình hoặc chạy nền.
- Khi đổi thiết bị phát âm thanh hoặc đổi mạng, mở lại ứng dụng và quét QR mới.

Xem hướng dẫn trong [README](https://github.com/BllakFoxV/lan-audio#readme)
và [lịch sử phát hành](https://github.com/BllakFoxV/lan-audio/blob/main/CHANGELOG.md).
