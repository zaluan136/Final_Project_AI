# Task 2 - Tank Battle

Chạy từ thư mục gốc của dự án:

```bash
python -m pip install -r task_2/requirements.txt
python -m task_2
```

Nên dùng Python 3.12 hoặc 3.13. Với Python 3.14 trên Windows, `pygame==2.6.1` có thể phải biên dịch từ mã nguồn và cài đặt thất bại.

Hoặc cài dependency của cả dự án bằng `python -m pip install -r requirements.txt`, chạy `python launcher.py` và chọn Task 2. Trong launcher, giao diện Pygame tự co giãn theo tỷ lệ; chạy riêng vẫn mở cửa sổ Pygame.

Khi chạy riêng trên Windows, Task 2 bật nhận biết DPI trước khi tạo cửa sổ để tránh Windows phóng mờ giao diện. Cửa sổ giữ kích thước vẽ 1200 × 820 pixel; kích thước vật lý trên màn hình phụ thuộc mật độ điểm ảnh.

Chạy kiểm thử bằng `python -m unittest task_2.test_contests`.
