# Task 3 — Kakuro CSP

Ứng dụng trình diễn Kakuro theo OOP, sử dụng Backtracking Search, Forward checking, MRV, Degree và LCV của Lecture 8. Hai đề được chép nguyên cấu trúc và clue từ `kakuro_demo.html` và `kakuro_task.html`; các tệp HTML giữ nguyên.

## Cài đặt và chạy

Môi trường khóa: **Python 3.14.7**, **PySide6 6.11.2**. Thực hiện từ thư mục `Final_Project_AI`, nơi chứa `task_3`.

Nếu terminal đang ở thư mục `Final_Task3`, vào đúng thư mục trước:

```powershell
cd Final_Project_AI
```

Lệnh `python -m task_3` cần chạy từ `Final_Project_AI`, không chạy từ thư mục cha hoặc bên trong `task_3`.

```sh
python -m venv .venv
```

Kích hoạt trên Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Kích hoạt trên macOS:

```sh
source .venv/bin/activate
```

Cài thư viện và chạy ứng dụng:

```sh
python -m pip install -r task_3/requirements.txt
python -m task_3
```

Trên macOS, dùng `python3` thay `python` để tạo môi trường nếu cần. Kiểm tra `python --version` trong môi trường là `3.14.7`. Tệp `.python-version` ghi phiên bản cho công cụ quản lý Python; bản thân tệp không tự cài Python.

PySide6 6.11.2 có wheel `macosx_13_0_universal2` cho Intel và Apple Silicon, hỗ trợ Python từ 3.10 đến trước 3.15. Xem [metadata chính thức của bản phát hành](https://pypi.org/pypi/PySide6/6.11.2/json). Đã kiểm thử trên Windows với Python 3.14.7 và PySide6 6.11.2; **chưa chạy trên macOS 13.7.8 Intel Core i5**. Cần chạy lại lệnh kiểm thử và mở UI trên máy chấm để xác nhận tương thích thực tế.

## Sử dụng UI

- Chọn Demo 5×5 hoặc đề chính thức 9×9.
- **Chạy** phát các sự kiện theo tốc độ thanh trượt; **Tạm dừng** giữ nguyên trạng thái.
- **Bước tiếp** thực hiện đúng một sự kiện. Một sự kiện có thể là chọn biến, thử số, loại domain hoặc khôi phục.
- **Đặt lại** hủy lượt giải hiện tại. Đổi đề cũng hủy lượt giải và tạo solver mới.
- Số nhỏ theo lưới 3×3 là domain; số lớn là giá trị đã gán. Singleton domain vẫn hiển thị nhỏ cho đến khi được gán.
- Ô viền đậm là ô đang xét. Các dãy liên quan có nền xám nhạt; bảng bên phải hiển thị clue và tổng đã gán.
- Log ghi nguyên nhân loại giá trị, domain rỗng và bước backtrack. Log giữ tối đa 1.200 dòng gần nhất.
- Nhãn **CHỌN Ô** giải thích MRV, Degree và thứ tự LCV. **GÁN THỬ** bắt đầu một nhánh; **FORWARD CHECKING** cho thấy domain trước và sau khi loại. **THẤT BẠI** báo nhánh không đi tiếp được; **BACKTRACK** báo giá trị bị bỏ và domain được khôi phục. Số ô đã gán thể hiện độ sâu hiện tại.

UI chỉ trình diễn thuật toán, không có nhập số thủ công. Toàn bộ màu dùng trắng, xám và đen; đường chéo clue được vẽ bằng `QPainter`.

## Mô hình CSP

Với mỗi ô trắng tại hàng `r`, cột `c`, tạo biến `X[r,c]`. Tọa độ nội bộ bắt đầu từ 0; UI hiển thị `R1C1` bắt đầu từ 1. Demo có 12 biến; đề chính thức có 48 biến.

Domain ban đầu của mỗi biến là `{1,2,3,4,5,6,7,8,9}`. Ô đen và ô clue không phải biến. Mỗi ô trắng thuộc đúng một dãy ngang và một dãy dọc.

Mỗi dãy có hai điều kiện: tổng các biến bằng clue, và mọi giá trị trong dãy khác nhau. Vì tổng liên quan nhiều biến, đây là CSP với ràng buộc nhiều ngôi. Không coi kiểm tra `Xi != Xj` là đủ để kiểm tra tổng.

## Thuật toán

1. Backtracking Search duyệt sâu, gán một biến mỗi lần. Chỉ chấp nhận trạng thái đầy đủ sau khi kiểm tra lại toàn bộ tổng, không trùng và miền 1–9.
2. MRV chọn biến chưa gán có domain nhỏ nhất. Degree phá hòa bằng số ô lân cận chưa gán lớn nhất; đếm mỗi ô một lần. Nếu vẫn hòa, chọn tọa độ nhỏ nhất theo hàng rồi cột.
3. LCV thử đánh giá từng giá trị trên bản sao assignment. Đếm số giá trị bị loại trực tiếp khỏi domain của các ô lân cận. Ưu tiên số lần loại ít nhất; hòa thì ưu tiên số nhỏ. Đánh giá này không thay đổi trạng thái thật và không cộng vào thống kê pruning.
4. Forward checking sau mỗi lần gán duyệt các ô chưa gán cùng dãy. Loại ứng viên nếu gây trùng hoặc làm tổng dãy không thể đạt. Khi một domain rỗng, dừng nhánh ngay. Đây là một lượt kiểm tra các ô lân cận, không phải AC-3 hay lan truyền đến điểm cố định.
5. Trước khi thử giá trị, sao chép domain của trạng thái cha. Khi thất bại, xóa phép gán đang thử và khôi phục toàn bộ domain. Assignment của các mức sâu được khôi phục khi quay lui qua từng mức.

Để kiểm tra tổng một phần, lấy tổng cần bù sau các giá trị đã gán. Với các ô còn lại, bỏ các số đã dùng khỏi domain. Cận dưới là giá trị lớn hơn giữa tổng các minimum theo ô và tổng `k` số nhỏ nhất trong hợp domain. Cận trên lấy tương tự bằng minimum của hai tổng maximum. Nếu thiếu `k` số phân biệt hoặc tổng cần bù nằm ngoài cận, loại ứng viên. Cách kiểm tra này an toàn nhưng có thể giữ lại ứng viên cuối cùng vẫn vô nghiệm; Backtracking xử lý các trường hợp đó. Không liệt kê mọi bộ hoán vị và không dùng thuật toán ngoài Lecture 8.

Backtracking có số nhánh tối đa theo cấp số mũ `9^n`. MRV, Degree, LCV và Forward checking giảm số nhánh thực tế, không thay đổi độ phức tạp xấu nhất. Mỗi dãy dài tối đa 9 ô. Bản sao domain tại mỗi độ sâu dùng bộ nhớ xấp xỉ `O(9n²)` trên đường tìm kiếm; log UI có giới hạn và không lưu toàn bộ lịch sử sự kiện.

Không dùng AC-3, Min-conflicts hay thuật toán tìm kiếm khác. Mục tiêu là tìm một lời giải hợp lệ, không chứng minh tính duy nhất.

## Kiến trúc và ghép launcher

- `Board`, `Cell`, `Run` biểu diễn dữ liệu; `KakuroCSP` kiểm tra ràng buộc và tạo domain.
- `KakuroSolver` không import PySide6. `solve()` trả assignment hoặc `None`; `events()` phát các snapshot độc lập để UI trình diễn. Mỗi solver chỉ chạy một lần.
- Sự kiện gồm `kind`, `cell`, `message`, `assignment`, `domains` và `statistics`. Các loại là `start`, `select`, `try`, `prune`, `failure`, `restore`, `complete`.
- `KakuroWidget(parent=None)` là widget ghép launcher. Import `from task_3 import KakuroWidget`, rồi thêm vào layout hoặc stacked widget của ứng dụng hiện có. Widget không tự tạo `QApplication` hay gọi `exec()`.
- Entry point `python -m task_3` tạo ứng dụng riêng. Không chỉnh Task 1 hoặc Task 2.

### Ghép Task 1 PySide6 và Task 2 Pygame

Đặt launcher tại thư mục chứa các package `task_1`, `task_2`, `task_3`. Dùng một `QApplication` và event loop Qt cho launcher và Task 1/3. Nếu Task 1 cung cấp một `QWidget`, thêm widget đó và `KakuroWidget` vào cùng `QStackedWidget`. Không gọi `QApplication` hoặc `app.exec()` lần nữa khi chuyển trang.

Chạy Task 2 Pygame trong **tiến trình riêng** bằng `QProcess`, để vòng lặp Pygame không chặn event loop Qt. Task 2 cần có entry point chạy độc lập; ví dụ bên dưới giả sử nhóm Task 2 cung cấp `python -m task_2`. Giữ tham chiếu `QProcess`, ngăn mở nhiều bản và xử lý đóng tiến trình khi launcher thoát:

```python
import sys
from pathlib import Path
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication, QPushButton, QStackedWidget, QVBoxLayout, QWidget
from task_3 import KakuroWidget

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout(window)
pages = QStackedWidget()
pages.addWidget(KakuroWidget())
layout.addWidget(pages)
button = QPushButton("Open Task 2")
layout.addWidget(button)
game = QProcess(window)
game.setProgram(sys.executable)
game.setArguments(["-m", "task_2"])
game.setWorkingDirectory(str(Path(__file__).resolve().parent))

def open_game():
    if game.state() == QProcess.ProcessState.NotRunning:
        game.start()

def stop_game():
    if game.state() != QProcess.ProcessState.NotRunning:
        game.terminate()
        if not game.waitForFinished(2000):
            game.kill()
            game.waitForFinished(1000)

button.clicked.connect(open_game)
app.aboutToQuit.connect(stop_game)
window.show()
sys.exit(app.exec())
```

Cài Pygame vào cùng môi trường Python hoặc chọn interpreter riêng qua `setProgram`. Kiểm tra `errorOccurred` và `finished` để báo lỗi khởi động hoặc mã thoát. Tên entry point, API widget Task 1 và đường dẫn thực tế cần xác nhận sau khi merge; ví dụ trên không giả định cấu trúc chưa có.

UI dùng `QTimer` để lấy một sự kiện mỗi tick, nhường event loop giữa các bước; không dùng vòng lặp giải toàn bộ trong slot. Phép tính một sự kiện vẫn chạy trên UI thread, phù hợp hai đề cố định đã đo; đây không phải cam kết độ trễ cho bảng lớn tùy ý. Đổi đề hoặc đặt lại đóng generator cũ.

## Kiểm thử và đánh giá

```sh
python -m unittest discover -s task_3/tests -v
python -m task_3.benchmark
```

Solver và kiểm thử solver dùng thư viện chuẩn, không cần PySide6:

```sh
python -m unittest task_3.tests.test_solver -v
```

Kiểm thử bao gồm đối chiếu toàn bộ ô/clue với HTML, xác minh lời giải độc lập, chạy lặp lại, kiểm tra heuristic, đề vô nghiệm, domain rỗng, clue bất khả thi, khôi phục domain/assignment, thời gian loại trừ khoảng nghỉ, và vòng đời UI. Kiểm thử UI dùng Qt offscreen; vẫn cần kiểm tra cửa sổ thực tế trên máy đích.

Số đo tham khảo trên môi trường Windows hiện tại:

| Đề             | Biến | Lần thử | Backtrack | Giá trị bị loại | Thời gian solver |
| -------------- | ---: | ------: | --------: | --------------: | ---------------: |
| Demo 5×5       |   12 |      12 |         0 |              86 |    khoảng 0,01 s |
| Chính thức 9×9 |   48 |     121 |        73 |           1.164 |    khoảng 0,12 s |

Thời gian cộng các khoảng xử lý `next()` của generator, gồm tính heuristic và snapshot, không tính vẽ UI hoặc chờ animation. Lần thử là phép gán được thực hiện; backtrack là lần khôi phục sau một phép gán thất bại. Số giá trị bị loại cộng trên mọi nhánh, kể cả các giá trị đã khôi phục rồi bị loại lần nữa. Thời gian thay đổi theo máy; benchmark in số đo của lượt chạy hiện tại.

Luật Kakuro tham khảo [Wikipedia](https://en.wikipedia.org/wiki/Kakuro); lựa chọn thuật toán theo Lecture 8 được chép trong `AGENTS.MD`.
