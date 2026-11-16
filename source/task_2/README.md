# Task 2 — Tank Battle

Game tank theo lượt dùng adversarial search. Có thể chơi AI với AI hoặc nhận quyền điều khiển một tank trong trận.

## Chạy game

Chạy lệnh từ thư mục gốc `Final_Project_AI`:

```bash
python -m pip install -r task_2/requirements.txt
python -m task_2
```

Để mở menu chung của ba task:

```bash
python -m pip install -r requirements.txt
python launcher.py
```

Chọn **Open** ở Tank Battle. Nút **Game menu** của launcher đưa về menu chung và pause trận hiện tại. Mở lại game rồi chọn **Resume** để tiếp tục.

Khuyến nghị Python 3.12 hoặc 3.13. Trên Windows, Pygame 2.6.1 có thể thiếu wheel phù hợp với Python 3.14. Chạy trong launcher sử dụng khung Qt có co giãn và xử lý DPI; chạy riêng mở cửa sổ Pygame.

## Bắt đầu trận

1. Nhấn **Load map...** và chọn file `.txt` bằng hộp thoại.
2. Có hai preset: `maps/01_small_1v1.txt` (9×7, hai tank) và `maps/02_medium_2v2.txt` (13×11, bốn tank). Cả hai đã đặt base và gán team cho tank.
3. Hoặc tự đặt hai base, từ hai đến bốn tank và wall. Mọi tank phải được gán team A/B trước khi Start.
4. Mỗi dòng tank có nút **Switch search algorithm** để đổi riêng thuật toán của tank đó.
5. Nhấn **START**: trận chạy ngay. **Reset match / Play again** cũng bắt đầu lại ngay.

Map hỗ trợ `.` = ô trống, `#` = wall, `A/B` = base, `a/b` = tank của phe tương ứng. File chỉ có `.` và `#` được tải như địa hình để người dùng tự đặt entity. **Export map...** mở hộp thoại chọn nơi lưu; hiện chỉ xuất địa hình, không lưu base và tank.

## Điều khiển và panel

- Click tank trên map hoặc dòng tank để chọn; nhấn **Take control** để chơi ngay. **Return to AI** trả quyền và tiếp tục chạy. Hành động đã chốt trong lượt vẫn được giữ.
- WASD hoặc phím mũi tên: di chuyển; Space: FIRE; X: STAY.
- **Pause / Resume** hoặc phím P: dừng/chạy; Esc: pause hoặc đóng biểu đồ. **One turn** chạy một lượt rồi pause.
- Khi tank do người chơi điều khiển đang chờ action hoặc phải chọn lại sau tranh ô, game chờ input thay vì tự bỏ lượt.
- **Hide panel** mở rộng map. Thanh TURN, Take control, Return to AI và Pause/Resume luôn hiện. Trước Start, các nút điều khiển được làm mờ.
- Panel trận chia thành Match Settings, Match Actions và Tanks & Search. **Back to setup** về thiết lập trận; khác với **Game menu** của launcher.
- Kết quả thắng/thua/hòa hiện trên nền map mờ, có Play again và Back to setup.

## Luật hiện tại

- Tank đi tối đa một ô theo bốn hướng mỗi lượt; FIRE và STAY là hai action còn lại. MOVE bị chặn vẫn đổi hướng.
- HP ban đầu: tank 6, base 9, wall 3. Mỗi hit gây một sát thương. Đạn đi tối đa ba ô mỗi lượt, kiểm tra từng ô và dừng khi va chạm.
- Các tank chọn action từ cùng snapshot đầu lượt. Không đổi chỗ hoặc bước vào ô tank khác đang chiếm đầu lượt.
- Cùng tranh ô trống: random đều, người thua chọn lại trong cùng lượt. **Player first ON** cho tank đang được người chơi điều khiển thắng tranh ô; OFF quay về random đều. Ô đã chốt không được tranh lại.
- FIRE hướng trực tiếp vào base cùng phe bị chặn. Đạn cùng phe chạm base bị hấp thụ, không trừ HP; sát thương giữa các tank cùng phe vẫn có.
- Một tank hoặc base của phe bị phá thì phe đó thua, kể cả còn đồng đội. Hai phe cùng thua trong một bước va chạm thì hòa.
- Mặc định giới hạn 300 lượt, chỉnh trong setup. Hết lượt xét số tank sống; bằng nhau thì hòa. Phá hủy được xét trước giới hạn lượt.
- Trúng đạn: tank/base nháy đỏ 150 ms. Wall có sprite nứt theo HP và sáu frame vỡ trong 270 ms. Hiệu ứng chạy theo thời gian hiển thị, không giữ hết lượt.

## AI và so sánh thuật toán

Bốn cấu hình: Minimax, Alpha–Beta, Heuristic Minimax, Heuristic Minimax + Alpha–Beta. Mặc định là cấu hình cuối. Switch search algorithm dùng được cả trước và trong trận; đổi trong trận áp dụng ở lần AI quyết định tiếp theo, giữ bộ nhớ tank.

Hai bản thuần tìm tới terminal; hai bản heuristic dừng ở độ sâu giới hạn. Vì game có action đồng thời và random tranh ô, search có thêm bước tính kỳ vọng trên kết quả phân xử. UCS hỗ trợ đánh giá đường đi/phá tường; không thay thế adversarial search.

Timer mặc định ON, 950 ms chung cho các AI trong một lượt, tính cả retry. Đây là giới hạn mềm. Iterative deepening giữ kết quả depth đã hoàn tất; nếu chưa hoàn tất thì dùng fallback hợp lệ. Nemesis chỉ dùng khi có ít nhất ba tank sống và là cách xấp xỉ để giảm nhánh tìm kiếm.

Lịch sử tối đa 10 lượt thật hạ ưu tiên bước lặp. Bộ đếm đứng tại chỗ không tiến triển bổ sung phạt heuristic từ lượt thứ tư: `min(48, 8 × (idle_turns − 3))`. Di chuyển được, bắn/đổi hướng có mục tiêu và nguy hiểm do đạn gần tank được bảo vệ. Không cấm hành động và không bảo đảm loại bỏ mọi bế tắc.

**Compare + charts** so sánh bốn cấu hình:

- Terminal scenarios: hai tình huống kết thúc sau một lượt.
- Same budget: cùng snapshot và ngân sách cho một quyết định. Tab này mở trước để so sánh theo map đang chọn.
- Có thể bấm **Compare + charts** ngay ở setup sau khi đặt đủ base/tank và gán đội, không cần START. Snapshot lượt 0 dùng Max turns đã nhập; thao tác đo không bắt đầu trận.
- Mặc định **10 lần lặp cho mỗi thuật toán**, thay đổi ở ô **Compare runs**. Một lần bấm Compare chạy đủ bốn thuật toán, không cần chơi lại trận nhiều lần.
- Hiển thị thời gian trung bình ± độ lệch chuẩn, lượt thăm node, node MAX/MIN thực sự mở rộng và depth hoàn tất; kèm timeout/fallback. Node mở rộng là lần xử lý MAX/MIN không kết thúc ở terminal/cutoff và sinh tổ hợp hành động con. Đây không phải số GameState khác nhau duy nhất.
- Các bộ đếm tính cả công việc lặp lại trong iterative deepening và phần tìm kiếm chưa hoàn tất. Cùng số node mở rộng vẫn có thể khác số nhánh con được xét và thời gian.
- Mỗi mẫu dùng cùng snapshot; thứ tự thuật toán được xoay giữa các lần lặp, cache UCS được xóa trước mỗi quyết định. Compare không bật memory, nemesis hay ưu tiên player.
- Khi trận đã kết thúc, Compare dùng snapshot của lượt ngay trước khi kết thúc, ghi rõ nguồn ở đầu biểu đồ. Không so sánh trực tiếp state kết thúc vì search sẽ trả ngay mà không mở rộng.
- Để lấy số liệu: dùng ba map 1v1 khác nhau, cùng budget (ví dụ 150 ms), depth (ví dụ 3) và 10 lần lặp; bấm Compare ngay ở setup (lượt 0), hoặc pause tại snapshot cần đo rồi bấm Compare một lần mỗi map. Ghi cả map, snapshot/lượt, cấu hình và máy đo. Ba map cho 120 quyết định Same budget. Terminal scenarios cố định không thay đổi theo map.
- Benchmark không đo win rate hay tổ chức giải đấu; không suy ra độ phức tạp Big-O chỉ từ thời gian đo.

Chạy benchmark từ terminal:

```bash
python -m task_2.benchmark
```

## Kiểm thử

```bash
python -m unittest discover -s task_2 -p "test*.py"
```

Các test bao gồm luật game, tranh ô/player priority, bảo vệ base cùng phe, chống đứng yên, benchmark, API bot ngoài và khung Qt. Kết quả test không chứng minh game không còn lỗi ở mọi bản đồ.

## Tổ chức code

| Phần | Trách nhiệm |
|---|---|
| `core/state.py`, `core/rules.py` | State, entity, luật và chuyển trạng thái. |
| `search/algorithms.py`, `evaluation.py` | MAX/MIN, Alpha–Beta, cutoff, utility và heuristic. |
| `search/tactics.py`, `agents.py` | UCS, priority và agent từng tank. |
| `memory/memory.py` | Lịch sử thật, priority chống lặp và phạt đứng yên. |
| `match/setup.py`, `runner.py` | Thiết lập, thu action, timer, retry và commit lượt. |
| `play.py`, `qt_widget.py`, `scaled_canvas.py` | UI Pygame và tích hợp Qt/DPI. |
| `asset/` | Sprite và script tạo asset. |
| `benchmark.py` | So sánh bốn cấu hình search. |

## Tình trạng tích hợp thuật toán ngoài

Đề gốc có yêu cầu cơ chế tích hợp thuật toán nhóm khác. Code còn `match/bot_loader.py` (`FileAgent`) và `match/example_bot.py`, với interface `choose_action(state, tank_id, draft, deadline)`. Bot lỗi/quá hạn/hành động không hợp lệ được runner thay bằng fallback.

**UI hiện không có nút import `.py`.** Người dùng chọn bốn thuật toán có sẵn trên từng dòng tank; tích hợp bot ngoài hiện cần dùng API trong code. Chưa có hệ thống giải đấu hoặc đo tỷ lệ thắng giữa các nhóm. Cần ghi đúng giới hạn này trong báo cáo.
