# Task 1 — N-Queens

Ứng dụng giải bài toán N-Queens bằng SAT hoặc Min-Conflicts và hiển thị lời giải trên bàn cờ. Bàn cờ được vẽ bằng PySide6; quân hậu dùng SVG.

## Cài đặt và chạy

Chạy các lệnh từ thư mục gốc của dự án:

```powershell
python -m pip install -r task_1/requirements.txt
python -m task_1
```

Hoặc cài dependency của cả hai task Qt bằng `python -m pip install -r requirements.txt`, sau đó chạy `python launcher.py`. Task 1 cũng có thể được mở từ launcher. Giao diện dùng widget PySide6 và style mặc định của hệ điều hành.

## Sử dụng

- Tab **Solve**: chọn kích thước bàn cờ và thuật toán, điều chỉnh tham số rồi nhấn **Solve N-Queens**. Nút **Reset board** xóa kết quả hiển thị.
- Tab **CNF analysis**: xem số biến và số mệnh đề lý thuyết của mã hóa pairwise theo kích thước bàn cờ.
- Tab **Benchmark**: chạy nhiều cấu hình SAT hoặc Min-Conflicts và xuất kết quả ra CSV.

SAT dùng `python-sat` với Glucose3. Min-Conflicts là tìm kiếm cục bộ có giới hạn số bước và số lần khởi tạo lại; không tìm được lời giải trong giới hạn không chứng minh bài toán vô nghiệm. Giao diện kiểm tra tính hợp lệ trước khi vẽ kết quả.

Thời gian solver và thời gian toàn bộ lượt chạy là các phép đo khác nhau. Phép giải và benchmark chạy trong worker Qt để giao diện tiếp tục xử lý sự kiện.

## Cấu trúc

- `app.py`: widget giao diện, bàn cờ và worker.
- `core.py`: Min-Conflicts và kiểm tra lời giải.
- `sat.py`: mã hóa CNF và gọi SAT solver.
- `experiments.py`: benchmark và xuất CSV.
- `__init__.py`: xuất `NQueensPage` để launcher nhúng vào `QStackedWidget`.
- `__main__.py`: tạo `QApplication` khi chạy độc lập.
- `tests/`: kiểm thử thuật toán.

```powershell
python -m unittest task_1.tests.test_core -v
```
