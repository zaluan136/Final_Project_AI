# Đối chiếu code với đề

Phạm vi: code, cách chạy và kiểm thử của ba task; không đánh giá báo cáo hay tính điểm. Xem [DEMO.md](DEMO.md) để thực hiện từng bước.

## Task 1 - N-Queens

| Yêu cầu                           | Bằng chứng trong code                                                           | Kết quả                   |
| --------------------------------- | ------------------------------------------------------------------------------- | ------------------------- |
| Biến logic và CNF                 | `task_1/sat.py`: biến cho mỗi ô; ràng buộc hàng, cột, đường chéo; PySAT CardEnc | Đã triển khai             |
| Glucose3 và thí nghiệm N tăng dần | `SATSolver`, `sat_experiments`, tab Benchmark; báo clause và thời gian solve    | Đã triển khai và kiểm thử |
| Min-Conflicts và heuristic        | `task_1/core.py`: standard và most-conflicted; `local_experiments` so sánh      | Đã triển khai và kiểm thử |

Kiểm thử SAT hiện bao gồm các encoding, N=2, 3 vô nghiệm và N=4, 8 có nghiệm; số clause pairwise còn được kiểm tra với N=4, 8, 12. Kết quả benchmark ngẫu nhiên và thời gian phụ thuộc môi trường.

## Task 2 - Tank Battle

| Yêu cầu                          | Bằng chứng trong code                                                                                            | Kết quả                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Luật game, HP và va chạm từng ô  | `core/state.py`, `core/rules.py`, `test_rules.py`                                                                | Đã triển khai và kiểm thử các trường hợp chính                                               |
| Minimax, Alpha-Beta và heuristic | `search/algorithms.py`, `search/agents.py`                                                                       | Có bốn cấu hình; tìm kiếm nhiều tank dùng dự đoán cho các tank không phải đối tượng đang xét |
| Thí nghiệm công bằng             | `benchmark.py`: cùng trạng thái và điều kiện trong mỗi suite; thống kê thời gian, nút, độ sâu, timeout, fallback | Có công cụ; cần diễn giải riêng suite terminal và budget                                     |
| UI Pygame và nạp bot             | `play.py`, `match/bot_loader.py`, `test_integration.py`                                                          | Có UI và giao diện bot; hai bot thử nghiệm cùng chơi một lượt                                |

Đội thua khi một tank hoặc base của đội bị phá; hai đội cùng thua trong một bước va chạm thì hòa. Minimax/Alpha-Beta thuần có thể timeout và chuyển sang fallback trong bài thử có ngân sách; đây không phải bằng chứng đã hoàn tất tìm kiếm. Bot thực tế của nhóm khác và giao diện trên macOS vẫn cần thử trực tiếp.

## Task 3 - Kakuro CSP

| Yêu cầu                                     | Bằng chứng trong code                                | Kết quả                                                                         |
| ------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| Biến, domain và ràng buộc                   | `model.py`: ô trắng, domain 1–9, tổng và không trùng | Đã triển khai                                                                   |
| Backtracking, propagation và heuristic      | `solver.py`: Forward Checking, MRV, Degree và LCV    | Đã triển khai; không dùng AC-3                                                  |
| Hai bảng và lời giải                        | `boards.py`, `tests/test_solver.py`, `benchmark.py`  | Có kiểm tra đối chiếu HTML và xác thực độc lập nghiệm; hai bảng tìm được nghiệm |
| Trực quan domain, propagation, backtracking | `ui.py`, `tests/test_ui.py`                          | Có hiển thị và kiểm thử sự kiện trên bảng 9×9                                   |

HTML là bản tham chiếu được nhập lại, không được ứng dụng parse lúc chạy. Kiểm thử đối chiếu HTML không tự chứng minh HTML khớp hình đề gốc; hai bảng đã được đối chiếu hình đề trong lần rà trước. Solver dừng ở nghiệm đầu và không chứng minh nghiệm duy nhất. Forward Checking hiện tại duyệt một lượt các ô lân cận, không lan truyền đến điểm cố định.

## Kiểm chứng chung và giới hạn

Chạy `python -m unittest discover -v` để kiểm thử toàn bộ; các lệnh demo và benchmark nằm trong [DEMO.md](DEMO.md). UI test dùng Qt offscreen nên không thay thế kiểm tra thao tác và trình bày trên màn hình thật. Chưa có kết quả chạy xác nhận trên macOS 13.7.8 Intel; không thể cam kết điểm số chỉ từ test tự động.
