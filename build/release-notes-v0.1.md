## LAN Audio 0.1

Bản public đầu tiên: truyền âm thanh PC Windows sang trình duyệt điện thoại trong LAN.

### Điểm nổi bật

- App portable Windows x64: không cần cài Python, driver âm thanh ảo hoặc ứng dụng điện thoại.
- Mở app là server chạy; giao diện gọn với QR, trạng thái và sao chép link.
- Thu âm WASAPI loopback và phát PCM qua Web Audio, có âm lượng và trạng thái kết nối.
- QR offline có token, lưu cookie phiên; link cũ hiện hướng dẫn ghép nối thay vì lỗi 403 mặc định.
- Có ADB đã cấp quyền thì tự mở link khi chưa có ai nghe. Mỗi thiết bị chỉ mở một lần trong suốt lần mở app.
- Đã kèm Python, QR, phần thu âm và ADB; có log để chẩn đoán lỗi.
- Tách mã nguồn / build / kiểm thử; 16 kiểm thử tự động đã qua.

### Tải và chạy

Tải `LAN-Audio-v0.1-Windows-x64.exe` rồi mở, hoặc giải nén ZIP và chạy `LAN Audio.exe`.
Cho phép truy cập mạng Private nếu Windows hỏi, quét QR và bấm **Bật nghe** trên điện thoại.
Đóng app để tắt server. `SHA256SUMS.txt` chứa checksum của hai gói tải về.

### Yêu cầu và giới hạn

Windows 10/11 64-bit, thiết bị đầu ra âm thanh hoạt động và điện thoại cùng LAN.
Trình duyệt vẫn cần một lần bấm để phát âm thanh; không bảo đảm phát khi khóa màn hình.
Đổi đầu ra âm thanh hoặc mạng cần mở lại app. HTTP dành cho LAN tin cậy.

Xem [README](https://github.com/BllakFoxV/lan-audio#readme) và
[CHANGELOG](https://github.com/BllakFoxV/lan-audio/blob/main/CHANGELOG.md).
