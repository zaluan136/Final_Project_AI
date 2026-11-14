# Introduction to Artificial Intelligence — Final Project

Đồ án gồm ba bài toán AI, có thể chạy riêng hoặc mở từ launcher chung:

- [Task 1 — N-Queens](task_1/README.md): giải và hiển thị bài toán N quân hậu bằng SAT hoặc Min-Conflicts.
- [Task 2 — Tank Battle](task_2/README.md): mô phỏng trận đấu xe tăng với các thuật toán tìm kiếm; giao diện dùng Pygame.
- [Task 3 — Kakuro CSP](task_3/README.md): minh họa quá trình giải Kakuro bằng Backtracking, Forward Checking, MRV, Degree và LCV.

## Cài đặt

Khuyến nghị dùng Python 3.12. Trên Windows, Pygame 2.6.1 có thể gặp lỗi biên dịch khi cài với Python 3.14. Các lệnh dưới đây chạy từ thư mục gốc dự án.

Tạo và kích hoạt môi trường ảo trên Windows PowerShell:

```powershell
winget install -e --id Python.Python.3.12
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Trên macOS hoặc Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

File `requirements.txt` cài dependency của cả ba task. Task 1 và 3 dùng cùng phiên bản PySide6; Task 2 dùng Pygame.

## Chạy ứng dụng

Mở launcher và chọn task ở thanh bên:

```bash
python launcher.py
```

Task 1 và 3 dùng theme chung `ui/themes.qss`. Task 2 được nhúng trong launcher và tự co giãn theo tỷ lệ khi đổi kích thước cửa sổ. Nội dung Pygame được vẽ ở độ phân giải 1200 × 820 rồi thu phóng mượt; chữ và hình có thể hơi mờ khi thu nhỏ. Giao diện Pygame không chịu ảnh hưởng của QSS. Có thể chạy từng task trực tiếp:

```bash
python -m task_1
python -m task_2
python -m task_3
```

## Kiểm thử

Chạy các kiểm thử hiện có từ thư mục gốc:

```bash
python -m unittest discover -v
```

Xem README của từng task để biết cách sử dụng, cấu trúc và các lệnh kiểm thử riêng.
