# Hướng dẫn demo đồ án Introduction to AI

Tài liệu này mô tả thao tác trên phiên bản code hiện tại. Các kết quả thời gian phụ thuộc máy; không cần khớp chính xác giữa các lần chạy.

## 1. Chuẩn bị trước buổi demo

Mở terminal tại thư mục gốc dự án. Khuyến nghị Python 3.12; cài dependency và chạy test:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -v
```

Trên macOS/Linux thay ba lệnh đầu bằng:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Chạy launcher bằng `python launcher.py`. Các trang Task 1, Task 2 và Task 3 nằm ở sidebar. Có thể chạy riêng bằng `python -m task_1`, `python -m task_2`, `python -m task_3`.

## 2. Task 1 - N-Queens

### A. Giải bằng Glucose3

1. Chọn **Task 1 - N-Queens** và tab **Solve**.
2. Đặt **Board size (N)** là 8, **Algorithm** là `SAT / Glucose3`, **SAT encoding** là `pairwise`; bỏ chọn **Break mirror symmetry**.
3. Nhấn **Solve N-Queens**. Đợi **Valid solution** và bàn cờ xuất hiện tám quân hậu.
4. Chỉ vào **CNF clauses**, **Variables** và **Solver time**. Với N=8, pairwise không bật symmetry có 64 biến gốc và 736 clause. Thời gian thay đổi theo máy.
5. Chuyển tab **CNF analysis**, đặt N=8 để giải thích: biến Boolean biểu thị mỗi ô; mỗi hàng có đúng một quân, mỗi cột và đường chéo có tối đa một quân. Các điều kiện được mã hóa thành CNF trước khi đưa vào Glucose3.

### B. Min-Conflicts và thí nghiệm

1. Về tab **Solve**, chọn **Algorithm** `Min-Conflicts`, **Local variable heuristic** `standard`, N=8, rồi nhấn **Solve N-Queens**.
2. Giải thích: chọn ngẫu nhiên một quân đang có xung đột, sau đó chuyển quân trong cột của nó tới hàng có ít xung đột nhất. Chỉ vào **Steps** và **Restarts**.
3. Đổi heuristic sang `most_conflicted`, giải lại: phiên bản này chọn quân có số xung đột lớn nhất, hòa thì chọn ngẫu nhiên. Min-Conflicts là thuật toán ngẫu nhiên; thất bại trong giới hạn bước không chứng minh vô nghiệm.
4. Mở **Benchmark**, chọn **Family** `SAT`, **Trials** 5, **N preset** `4,8,12,16`, rồi nhấn **Run benchmark**. Đọc số clause, thời gian solve và tổng thời gian. Có thể nhấn **Export CSV** để lưu.
5. Đổi **Family** thành `LOCAL`, giữ cùng N và số trials, chạy lại. So sánh `standard` và `most_conflicted` theo success, thời gian; không khẳng định một phương pháp luôn nhanh hơn khi dữ liệu chưa chứng minh.

## 3. Task 2 - Tank Battle

### A. Tải bản đồ và chạy trận

1. Chọn **Task 2 - Tank Battle**. Nhấn **Load map...**, chọn `task_2/maps/01_small_1v1.txt`. Bản đồ mẫu đã có hai base và hai tank được chia đội.
2. Có thể chọn một tank trên bảng hoặc dòng tank, nhấn **Cycle selected AI** để đổi giữa Minimax, Alpha-Beta, Heuristic Minimax và Heuristic + AB. Mặc định là Heuristic + AB.
3. Đặt **AI budget (ms)** và **Depth** theo cấu hình cần thử; giữ Timer ON. Nhấn **START**: trận chạy ngay. Nhấn **Pause** hoặc phím `P` để tạm dừng; **One turn** chạy một lượt rồi dừng.
4. Chỉ vào số lượt, HP và đạn. Mỗi lượt tank di chuyển tối đa một ô; đạn đi tối đa ba ô và kiểm tra va chạm từng ô. Tank/base/wall ban đầu có HP 6/9/3, mỗi hit trừ 1 HP.
5. Đội thua khi một tank hoặc base của đội đó bị phá; nếu cả hai đội cùng thua trong một bước va chạm thì hòa. Chọn `task_2/maps/02_medium_2v2.txt` để minh họa nhiều tank nếu cần.

### B. Điều khiển và so sánh thuật toán

1. Trong trận, chọn một tank rồi nhấn **Take control**. Dùng WASD hoặc phím mũi tên để di chuyển, `Space` để bắn, `X` để đứng; chọn **Return to AI** để trả quyền cho AI.
2. Nhấn **Compare + charts**, đợi kết quả. Chọn **Terminal scenarios** để xem các tình huống kết thúc sau một lượt; chọn **Same budget** để xem cùng giới hạn thời gian cho một quyết định.
3. So sánh thời gian trung bình, số nút và độ sâu hoàn thành của bốn cấu hình. Đọc cả số **timeout** và **fallback**; Minimax thuần có thể không hoàn tất trong ngân sách. Nhóm thử này không đo tỉ lệ thắng cả trận. Nhấn **Close** để đóng biểu đồ; dùng **Resume** nếu trận đang tạm dừng.

### C. Bot từ nhóm khác

1. Tại màn hình setup, chọn một tank và nhấn **Load .py for tank**. Chọn `task_2/match/example_bot.py` hoặc file bot tuân thủ giao diện trong README Task 2.
2. Chọn tank còn lại, nạp bot khác hoặc để AI có sẵn, rồi nhấn **START**. Hai thuật toán cùng nhận trạng thái của một môi trường game.
3. File bot cần hàm `choose_action(state, tank_id, draft, deadline)` trả `Action` hoặc tên hành động. Nếu bot lỗi, không hợp lệ hoặc quá thời gian, game dùng hành động dự phòng. Test tự động đã dùng hai bot mẫu độc lập; nhóm vẫn nên thử file thực tế của nhóm bạn.

## 4. Task 3 - Kakuro CSP

### A. Bảng Demo 5×5

1. Chọn **Task 3 - Kakuro**, chọn **Demo 5×5**. Các số nhỏ trong ô trắng là domain ban đầu 1–9.
2. Chọn tốc độ 0.5× hoặc 1×; nhấn **Step** từng lần. Quan sát **Current step**, ô có viền đậm, các dãy tô xám và **History**.
3. Khi xuất hiện `TRY`, chỉ số lớn trong ô là giá trị đã gán. Khi có `PRUNE`, chỉ các ứng viên bị loại và các số còn lại trong domain. Hai dãy ngang/dọc của ô đều phải thỏa tổng clue và không có số trùng.
4. Nhấn **Run** để tiếp tục, **Pause** để dừng, **Reset** để bắt đầu lại. Khi hoàn tất, xem trạng thái lời giải và thống kê.

### B. Bảng Assignment 9×9

1. Chọn **Assignment 9×9**, nhấn **Run** và tăng lên 4× nếu muốn đến đoạn quay lui nhanh hơn. Nhấn **Pause** khi thấy `BACKTRACK` trong History.
2. Giải thích: MRV chọn domain nhỏ nhất; Degree phá hòa theo số hàng xóm chưa gán; LCV thử giá trị dự kiến loại ít ứng viên nhất. Forward Checking kiểm tra hàng xóm sau phép gán; Backtracking khôi phục domain và thử nhánh khác khi thất bại.
3. Cho chạy đến **Search complete**. Nếu History đã dài, log tự giới hạn số dòng. Có thể chạy `python -m task_3.benchmark` trong terminal để kiểm tra cả hai bảng và thống kê.
4. Nói rõ solver tìm một nghiệm hợp lệ, chưa chứng minh nghiệm duy nhất. Forward Checking hiện tại duyệt một lượt hàng xóm, không phải AC-3.

## 5. Kiểm tra trước khi trình bày

- Test toàn dự án: `python -m unittest discover -v`.
- Benchmark Task 2: `python -m task_2.benchmark`; benchmark Task 3: `python -m task_3.benchmark`.
- Đảm bảo tài nguyên, font và cửa sổ hiển thị tốt trên máy dùng demo. Máy đánh giá theo đề là macOS Ventura Intel; cần chạy thử trực tiếp trên máy đó nếu có.
- Nếu cần trình bày thời gian hay so sánh, dùng kết quả thực tế của máy vừa chạy và nêu rõ cấu hình, số lượt thử, timeout và giới hạn.
