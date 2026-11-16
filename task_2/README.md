# Task 2 - Tank Battle

Chạy từ thư mục gốc của dự án:

```bash
python -m pip install -r task_2/requirements.txt
python -m task_2
```

Nên dùng Python 3.12 hoặc 3.13. Với Python 3.14 trên Windows, `pygame==2.6.1` có thể phải biên dịch từ mã nguồn và cài đặt thất bại.

Hoặc cài dependency của cả dự án bằng `python -m pip install -r requirements.txt`, chạy `python launcher.py` và chọn Task 2. Trong launcher, giao diện Pygame tự co giãn theo tỷ lệ; chạy riêng vẫn mở cửa sổ Pygame.

Khi chạy riêng trên Windows, Task 2 bật nhận biết DPI trước khi tạo cửa sổ để tránh Windows phóng mờ giao diện. Cửa sổ giữ kích thước vẽ 1200 × 820 pixel; kích thước vật lý trên màn hình phụ thuộc mật độ điểm ảnh.

Chạy kiểm thử bằng `python -m unittest task_2.test_rules task_2.test_integration task_2.test_contests task_2.test_stagnation task_2.test_qt_widget`.

Mỗi đội thua ngay khi một tank hoặc căn cứ của đội đó bị phá. Nếu cả hai đội cùng thua trong một bước va chạm, trận đấu hòa.

## Bot của nhóm khác

Chọn tank trong màn hình setup, nhấn **Load .py for tank**, rồi chọn file bot. File phải định nghĩa `choose_action(state, tank_id, draft, deadline)` và trả về một `task_2.core.state.Action` hoặc tên enum như `"FIRE"`, `"MOVE_UP"`, `"STAY"`. Xem `task_2/match/example_bot.py` để bắt đầu. `state` là trạng thái trận đấu, `draft` chứa các lượt chưa hoàn tất và các ô đã được giữ chỗ; `deadline` là hạn tính theo `time.perf_counter()` hoặc `None`. Bot lỗi, trả hành động không hợp lệ hoặc vượt thời gian sẽ được thay bằng hành động dự phòng.

**Compare + charts** so sánh bốn cấu hình trên cùng trạng thái trong từng nhóm thử nghiệm. Nhóm terminal dùng tình huống kết thúc sau một lượt; nhóm budget đo một quyết định với cùng giới hạn thời gian. Timeout và fallback được tính trong kết quả; đây không phải giải đấu hay phép đo tỷ lệ thắng.
