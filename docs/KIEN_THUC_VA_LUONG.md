# Kiến thức và luồng hoạt động của đồ án

Tài liệu này hỗ trợ đọc code, chuẩn bị vấn đáp và chọn nội dung đưa vào `report.tex`. Số liệu thời gian phải lấy từ thí nghiệm thực tế; không coi các ví dụ dưới đây là kết luận hiệu năng. Thao tác demo cụ thể nằm trong [DEMO.md](../DEMO.md).

## 1. Tổng quan hệ thống

`launcher.py` tạo `QApplication`, cửa sổ và sidebar. Task 1 và Task 3 là widget PySide6 nhúng vào `QStackedWidget`. Task 2 là game Pygame: khi mở trong launcher, `TankBattleWidget` nhận sự kiện Qt, chuyển tọa độ và phím sang Pygame, vẽ game lên surface rồi hiển thị frame trong Qt. Khi chạy `python -m task_2`, game mở cửa sổ Pygame riêng. Cả ba task cũng có entry point riêng qua `python -m task_1`, `python -m task_2`, `python -m task_3`.

Theo hướng đối tượng, mỗi task có các lớp giữ dữ liệu, thực thi thuật toán và quản lý giao diện. Đây là ứng dụng desktop gồm các module, không phải hệ microservices hay các dịch vụ giao tiếp qua mạng.

## 2. Task 1 - N-Queens

### Bài toán và công thức logic

Đặt N quân hậu trên bàn N×N sao cho không có hai quân cùng hàng, cột hoặc đường chéo. Mỗi ô `(r,c)` có biến Boolean `Q[r,c]`: true nếu có hậu. `square_var(n,r,c) = r*n+c+1` ánh xạ ô thành số nguyên dương cho PySAT.

CNF là phép AND của các clause; mỗi clause là phép OR của các literal. Với từng hàng, một clause chứa tất cả biến của hàng đảm bảo ít nhất một hậu. Với hai ô tấn công nhau trong cùng một nhóm, clause `¬Qi ∨ ¬Qj` loại trường hợp cả hai có hậu. Áp dụng at-most-one cho mỗi hàng, cột và cả hai hướng đường chéo. Đúng một hậu mỗi hàng cộng với tối đa một hậu mỗi cột đảm bảo đúng N hậu trên N cột.

`CNFEncoder` dùng `CardEnc.atmost` của PySAT với pairwise, sequential counter hoặc ladder. Pairwise tạo clause nhị phân cho từng cặp; hai encoding còn lại có thể thêm biến phụ. Tùy chọn symmetry giới hạn hậu ở hàng đầu vào nửa trái kể cả ô giữa, dựa trên đối xứng gương; tùy chọn này giữ khả năng tìm một nghiệm nếu có, không phù hợp để đếm toàn bộ nghiệm.

### Luồng SAT

1. UI lấy N, encoding và symmetry; `SolveWorker` chạy nền để UI không đứng.
2. `CNFEncoder.encode()` tạo các nhóm và clause, ghi thời gian dựng CNF.
3. `SATSolver.solve()` khởi tạo `Glucose3` với clause, đo riêng thời gian khởi tạo và `solver.solve()`.
4. Nếu SAT, giải mã literal dương của N² ô thành danh sách hàng theo từng cột; `verify_solution` kiểm tra hàng và hai đường chéo trước khi vẽ.
5. Tab CNF analysis hiển thị số clause pairwise lý thuyết; tab Benchmark chạy các N và encoding, tổng hợp kết quả và có thể xuất CSV.

Không nhầm thời gian solve với thời gian tổng: tổng benchmark cộng thời gian dựng CNF, khởi tạo solver và solve. Công thức số clause pairwise không symmetry là `N + N²(N−1) + N(N−1)(2N−1)/3`; với N=8 là 736. Code hiện duyệt các ô cho từng đường chéo, không phải chỉ duyệt một lần để lập tất cả nhóm.

### Min-Conflicts

Trạng thái là danh sách `queens[c] = r`, luôn có một hậu mỗi cột. Ba mảng đếm số hậu theo hàng và hai đường chéo. Số xung đột của hậu tại `(r,c)` là `row_count[r] + diag_a[r-c+N-1] + diag_b[r+c] - 3`; trừ 3 để bỏ chính hậu đó trong ba mảng.

Mỗi bước: tìm hậu có xung đột; `standard` chọn ngẫu nhiên một hậu trong số đó, `most_conflicted` chọn ngẫu nhiên trong số hậu có nhiều xung đột nhất. Thử các hàng của cột đó và chọn ngẫu nhiên giữa các hàng có ít xung đột nhất. Sau giới hạn bước, khởi tạo lại tối đa số lần quy định. Không tìm được nghiệm trong ngân sách không chứng minh vô nghiệm. Benchmark dùng cùng dãy seed và số lần thử cho hai chiến lược; kết quả ngẫu nhiên cần so cả tỉ lệ thành công, bước và thời gian.

## 3. Task 2 - Tank Battle

### Trạng thái và luật

`GameState` lưu kích thước, tank, base, wall, bullet, turn và max_turns. Tank có id, tọa độ, hướng, team và HP. Tank/base/wall ban đầu có HP 6/9/3; mỗi đạn trúng trừ 1. Sáu hành động là bốn hướng di chuyển, FIRE và STAY. Khi chọn hướng di chuyển, tank đổi hướng; nếu ô đích trống hợp lệ thì đi một ô, nếu bị chặn thì giữ vị trí.

Mỗi lượt thu thập hành động đồng thời. Các tank cùng chọn một ô trống được xử lý bằng xổ chọn; tank thua chọn lại, các ô đã giữ chỗ không được chọn lại. Tùy chọn player priority có thể ưu tiên tank người chơi. `GameRules.execute` xử lý di chuyển, va chạm với đạn có sẵn, sinh đạn mới, sau đó đẩy đạn tối đa ba ô, kiểm tra va chạm sau từng ô. Đạn trúng tank, base hoặc wall dừng ngay. Một tank hoặc base của đội bị phá khiến đội đó thua; hai đội cùng thua trong một bước va chạm là hòa. Khi hết lượt tối đa, code so số tank còn sống; đây là quy tắc bổ sung của implementation.

### Mô hình tìm kiếm và luồng trận

Hai đội là hai phía đối kháng; `terminal_value` trả +100000 khi đội đang xét thắng, -100000 khi thua và 0 khi hòa. Với trạng thái chưa kết thúc tại ngưỡng tìm kiếm, `evaluate` tính điểm đội mình trừ đội đối phương, dựa trên HP, số tank, khoảng cách, đường đi, nguy cơ đạn và căn cứ. Giá trị heuristic được giới hạn để kết quả kết thúc chiếm ưu tiên.

`MatchSetup` đọc map, đặt base/tank và phân đội. `MatchRunner` giữ trạng thái, `Draft` và cấu hình; `collect()` lấy đề xuất từ AI hoặc chờ người chơi, xử lý tranh ô và các lượt chọn lại; `commit()` áp dụng hành động bằng `GameRules`, cập nhật trạng thái và lịch sử. UI điều khiển pause, resume, step và hiển thị kết quả. AI tính trong worker để giao diện tiếp tục xử lý sự kiện.

`Searcher` xét lựa chọn tank đang điều khiển ở nút MAX và các phản ứng đối phương ở nút MIN. Alpha-Beta cắt nhánh không thể cải thiện kết quả. Vì có xổ chọn tranh ô, code tính kỳ vọng theo xác suất các kết quả và không truyền cửa sổ Alpha-Beta hẹp qua nút ngẫu nhiên. Khi có nhiều tank, các tank không thuộc tập đang xét được dự đoán bằng chính sách đơn giản; tùy chọn nemesis có thể chọn một đối thủ. Do đó đây là mô hình xấp xỉ cho trận nhiều tank, không nên nói luôn tính tối ưu chính xác toàn bộ hành động đồng thời.

Bốn cấu hình là Minimax, Alpha-Beta, Heuristic Minimax và Heuristic + Alpha-Beta. Bản thuần tìm tới trạng thái kết thúc; bản heuristic cắt theo độ sâu và dùng hàm đánh giá. Deadline có thể làm tìm kiếm dừng sớm; kết quả dự phòng không phải kết quả minimax đã hoàn tất. Bộ nhớ di chuyển và ưu tiên chiến thuật giúp hạn chế lặp hoặc đứng vô ích nhưng không đảm bảo tránh mọi vòng lặp.

### Benchmark và bot ngoài

`benchmark.compare()` có suite terminal gồm hai trạng thái kết thúc sau một lượt, và suite budget dùng cùng trạng thái, giới hạn thời gian mỗi quyết định. Mỗi cấu hình được đo thời gian, nodes, depth, timeout, fallback và số mẫu; timed-out samples vẫn được tính. Terminal suite giúp so sánh trong trường hợp tìm tới kết thúc, nhưng không đại diện tất cả trận. Budget suite không phải giải đấu hoặc tỉ lệ thắng; độ sâu giữa các cấu hình có thể khác. Nodes là số lần bộ đếm `check()` được gọi, không nhất thiết là số trạng thái duy nhất.

File bot ngoài phải cung cấp `choose_action(state, tank_id, draft, deadline)`, trả enum `Action` hoặc tên enum. `FileAgent` chạy bot bằng process riêng; lỗi, timeout hoặc hành động không hợp lệ dẫn tới fallback trong runner. Xem `task_2/match/example_bot.py` và README Task 2. Cần thử với bot thực tế của nhóm khác trước khi khẳng định tương thích.

## 4. Task 3 - Kakuro

### CSP và mô hình dữ liệu

Một ô trắng là biến `X`, domain ban đầu `{1,…,9}`. Mỗi dãy liên tục theo clue gọi là run. Với mỗi run, tổng các biến bằng clue và mọi số khác nhau. Hai ô cùng run là hàng xóm; mỗi ô trắng phải thuộc đúng một run ngang và một run dọc. Ví dụ run hai ô tổng 4 cho phép `(1,3)` hoặc `(3,1)`, không cho `(2,2)`.

`Cell` lưu loại ô và clue; `Board` tạo các `Run` và kiểm tra cấu trúc; `KakuroCSP` tạo domain, hàng xóm và kiểm tra ràng buộc. Hai bảng được định nghĩa trực tiếp trong `boards.py`; các HTML là bản tham chiếu, không được parse lúc chạy. Tọa độ code bắt đầu từ 0, nhãn UI từ 1.

`run_possible` loại trường hợp số đã gán trùng, domain rỗng, không đủ chữ số khác nhau hoặc tổng còn thiếu ngoài cận dưới/trên tính từ domain. Nếu tổng còn trong khoảng, chỉ có nghĩa là chưa phát hiện mâu thuẫn; không chứng minh tồn tại tổ hợp thỏa mọi domain. `is_solution` kiểm tra đầy đủ các ô, tổng và khác nhau sau khi gán xong.

### Luồng giải và UI

1. `KakuroSolver` tạo assignment rỗng và domain ban đầu. `events()` phát snapshot cho UI, còn `solve()` tiêu thụ các sự kiện để trả nghiệm.
2. `select_variable()` dùng MRV: chọn domain nhỏ nhất; nếu hòa dùng Degree là số hàng xóm chưa gán, sau đó tọa độ.
3. `order_values()` dùng LCV: thử từng giá trị nhất quán, đếm ứng viên hàng xóm sẽ bị loại, ưu tiên ít loại nhất; nếu hòa chọn số nhỏ hơn.
4. Backtracking lưu domain, gán giá trị, rồi Forward Checking duyệt một lượt hàng xóm và loại ứng viên không còn nhất quán. Domain rỗng làm nhánh thất bại.
5. Khi thất bại, bỏ phép gán và khôi phục domain; thử giá trị khác. Khi gán đủ, xác thực nghiệm; solver dừng ở nghiệm hợp lệ đầu tiên.
6. UI dùng `QTimer` lấy từng `SolverEvent`: start, select, try, prune, failure, restore, complete. Bàn vẽ domain, giá trị gán và dãy liên quan; history hiển thị các sự kiện. Thời gian solver không tính thời gian chờ giữa các frame, nhưng mỗi đoạn tính vẫn chạy trên luồng UI.

Không mô tả Forward Checking này là AC-3: code không chạy hàng đợi cung tới điểm cố định. Không khẳng định nghiệm duy nhất hoặc heuristic luôn tăng tốc nếu chưa có thí nghiệm đối chứng.

## 5. Viết vào report.tex và chuẩn bị vấn đáp

Giữ báo cáo trong giới hạn đề: tối đa 5 trang hai cột. Với mỗi task, viết ngắn: mô hình → thuật toán thực sự dùng → thiết lập thí nghiệm → số liệu đã đo → nhận xét và giới hạn. Báo số lần chạy, thông số và đơn vị; không sao chép thời gian của máy khác hoặc bịa kết quả. Các công thức, mô tả và số liệu Task 1 đã viết trong `report.tex` cần được đối chiếu lại với code hiện tại trước khi nộp.

Task 2 cần nêu rõ luật hành động đồng thời, xổ chọn, cách xử lý nhiều tank và fallback; Task 3 cần nêu domain, tổng, AllDifferent, cách chọn biến/giá trị, kiểm tra nghiệm và giới hạn một nghiệm. Trích dẫn bài giảng hoặc tài liệu thực sự sử dụng theo IEEE; không tự đoán metadata nguồn.

Một số câu hỏi cần tự trả lời được: Vì sao CNF biểu diễn đúng N hậu? MRV khác LCV thế nào? Khi nào forward checking thất bại? Tại sao Minimax thuần timeout vẫn có hành động? Alpha-Beta cắt nhánh nào? Thời gian benchmark có gồm thời gian dựng mô hình hay thời gian chờ UI không? Hai chế độ benchmark Task 2 có đo tỉ lệ thắng không? Các câu trả lời phải khớp code và dữ liệu vừa chạy, không khẳng định đã kiểm tra macOS Ventura Intel nếu chưa thực hiện.
