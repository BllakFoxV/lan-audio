# Changelog

## [0.1] — 2026-11-10

Bản phát hành public đầu tiên của LAN Audio cho Windows x64.

### Added

- Thu âm thanh thiết bị phát mặc định qua WASAPI loopback, không dùng microphone.
- Truyền PCM float32 tới web client qua HTTP trong LAN, tối đa hai kênh.
- Web client có bật/dừng nghe, âm lượng và trạng thái kết nối.
- Ghép nối bằng QR offline hoặc sao chép link có token.
- Lưu cookie phiên sau khi quét QR; xác thực riêng cho status và stream.
- Tự mở link qua ADB khi chưa có ai nghe, chỉ một lần cho mỗi thiết bị trong một lần mở app.
- Portable EXE cho Windows 10/11 x64, kèm Python, thư viện QR, WASAPI helper và ADB.
- Gói ZIP, checksum SHA-256 và nhật ký lỗi có giới hạn dung lượng.
- Kiểm thử tự động cho giao thức, vòng đời server, xác thực và chống lặp ADB.

### Changed

- Giao diện tối giản: QR, trạng thái, sao chép link; chỉ hiện chọn IP khi có nhiều địa chỉ.
- Server tự chạy khi mở app; đóng cửa sổ để tắt và dọn tiến trình nền.
- Tách mã nguồn `app/`, cấu hình `build/`, kiểm thử `tests/` và sản phẩm `dist/`.

### Fixed

- Link thiếu hoặc hết hạn mở trang hướng dẫn ghép nối thay vì trang lỗi 403 mặc định.
- Thiết bị ADB chưa bấm nghe không bị mở trình duyệt lặp vô hạn.
- Dọn tiến trình thu âm và worker ADB khi đóng app.
- Kiểm tra cổng trước khi mở tiến trình thu âm.

### Known limitations

- Cần LAN tin cậy; HTTP không mã hóa.
- Trên điện thoại vẫn cần bấm Bật nghe; không bảo đảm phát khi khóa màn hình/chạy nền.
- Đổi thiết bị phát hoặc mạng cần mở lại app; nội dung được bảo vệ có thể không thu được.

[0.1]: https://github.com/BllakFoxV/lan-audio/releases/tag/v0.1
