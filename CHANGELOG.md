# Lịch sử phát hành

## [0.1] — 2026-11-10

Bản phát hành đầu tiên của LAN Audio cho Windows 10/11 64-bit.

### Tính năng

- Chia sẻ âm thanh từ thiết bị phát mặc định của Windows đến trình duyệt qua LAN.
- Tự bắt đầu chia sẻ khi mở ứng dụng và kết thúc khi đóng cửa sổ.
- Kết nối bằng QR hoặc sao chép link có token truy cập.
- Chọn IP khi máy tính có nhiều địa chỉ mạng.
- Bật/dừng nghe, chỉnh âm lượng và xem trạng thái trên trang nghe.
- Tự mở link trên thiết bị Android đã cấp quyền ADB khi chưa có ai nghe;
  mỗi thiết bị được thử mở một lần trong mỗi lần chạy ứng dụng.
- Cung cấp file EXE, ZIP và checksum SHA-256.

### Lưu ý

- Cần mạng LAN tin cậy vì kết nối HTTP không mã hóa.
- Điện thoại cần bấm **Bật nghe**; trình duyệt có thể dừng âm thanh khi chạy nền
  hoặc khóa màn hình.
- Khi đổi thiết bị phát âm thanh hoặc đổi mạng, cần mở lại ứng dụng và quét QR mới.

[0.1]: https://github.com/BllakFoxV/lan-audio/releases/tag/v0.1
