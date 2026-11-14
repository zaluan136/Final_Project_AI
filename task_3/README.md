# Task 3 — Kakuro CSP

Ứng dụng minh họa quá trình giải Kakuro bằng Backtracking Search kết hợp Forward Checking, MRV, Degree và LCV. Hai bàn chơi lấy cấu trúc và clue từ `boards/kakuro_demo.html` và `boards/kakuro_task.html`.

## Cài đặt và chạy

Chạy từ thư mục gốc của dự án:

```powershell
python -m pip install -r task_3/requirements.txt
python -m task_3
```

Có thể cài dependency của cả dự án bằng `python -m pip install -r requirements.txt`, rồi chạy `python launcher.py` và chọn Task 3. Trên macOS hoặc Linux, dùng `python3` nếu lệnh Python của máy có tên đó. Kiểm tra phiên bản Python tương thích với PySide6 được khóa trong `requirements.txt`.

Giao diện dùng PySide6 Widgets với style mặc định của hệ điều hành, không dùng QSS hay thư viện theme. Bàn Kakuro được vẽ bằng `QPainter` với màu trắng, xám và đen; các icon điều khiển dùng SVG.

## Cách dùng

- Chọn bàn Demo 5×5 hoặc bàn chính thức 9×9.
- **Chạy** phát lần lượt các sự kiện; **Tạm dừng** giữ trạng thái; **Bước tiếp** xử lý một sự kiện.
- Thanh tốc độ điều chỉnh khoảng chờ giữa các sự kiện. **Đặt lại** hoặc đổi bàn sẽ bắt đầu một lượt giải mới.
- Số nhỏ là domain; số lớn là giá trị đã gán. Viền đậm đánh dấu ô đang xét và nền xám nhạt đánh dấu dãy liên quan.
- Bảng bên phải hiển thị trạng thái, thống kê và log. Log giữ tối đa 1.200 dòng.

Ứng dụng minh họa solver, không có chức năng nhập số thủ công.

## Mô hình và thuật toán

Mỗi ô trắng là một biến có domain ban đầu từ 1 đến 9. Mỗi dãy ngang hoặc dọc phải có tổng bằng clue và không chứa số trùng. Tọa độ trong code bắt đầu từ 0; giao diện hiển thị từ 1.

Solver chọn ô chưa gán bằng MRV; Degree phá hòa theo số ô lân cận chưa gán, sau đó dùng thứ tự tọa độ. LCV ưu tiên giá trị loại ít lựa chọn của các ô lân cận nhất. Sau mỗi phép gán, Forward Checking loại ứng viên không còn phù hợp; khi nhánh thất bại, Backtracking khôi phục assignment và domain của trạng thái cha.

Đây là một lượt kiểm tra các ô lân cận, không phải AC-3 hoặc lan truyền đến điểm cố định. Solver tìm một lời giải hợp lệ, không chứng minh tính duy nhất. Thời gian thống kê là thời gian xử lý solver, không gồm thời gian chờ animation.

## Cấu trúc và tích hợp

- `model.py`: dữ liệu bàn chơi và các kiểm tra ràng buộc CSP.
- `boards.py` và `boards/`: định nghĩa hai bàn và HTML tham chiếu.
- `solver.py`: solver độc lập với PySide6; `events()` phát snapshot cho giao diện.
- `ui.py`: `KakuroWidget`, bàn cờ, điều khiển và log.
- `__main__.py`: tạo `QApplication` khi chạy độc lập.
- `benchmark.py`: chạy solver và in thống kê.

Launcher nhúng `KakuroWidget` từ package `task_3` vào `QStackedWidget`. Widget không tự tạo `QApplication`. UI dùng `QTimer` để xử lý từng sự kiện; mỗi sự kiện vẫn được tính trên luồng UI.

## Kiểm thử

```powershell
python -m unittest discover -s task_3/tests -v
python -m task_3.benchmark
```

Kiểm thử solver có thể chạy riêng mà không mở cửa sổ:

```powershell
python -m unittest task_3.tests.test_solver -v
```

Kiểm thử UI sử dụng Qt offscreen; cần chạy ứng dụng trên hệ điều hành đích để xem cách hiển thị thực tế.
