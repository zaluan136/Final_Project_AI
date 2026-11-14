# Hướng dẫn đóng góp báo cáo

File báo cáo đang điền là [`report.tex`](report.tex). [`TASK.MD`](TASK.MD) ghi yêu cầu của đề; `report_ieee_format.tex` là mẫu IEEE tham khảo. Giữ định dạng `IEEEtran` hai cột và bảo đảm PDF cuối cùng không quá **5 trang**, bao gồm hình, bảng và tài liệu tham khảo.

## Phần mỗi thành viên cần chuẩn bị

Mỗi người phụ trách một task điền mục tương ứng trong `report.tex`, hoặc gửi nội dung cho người ghép báo cáo để tránh conflict:

| Task | Mục trong báo cáo                             | Nội dung cần điền                                                            |
| ---- | --------------------------------------------- | ---------------------------------------------------------------------------- |
| 1    | `N-Queens with SAT and Local Search`          | Bài toán, mã hóa SAT, Min-Conflicts, thí nghiệm và kết quả.                  |
| 2    | `Adversarial Search for Tank Battle`          | Trạng thái, hành động, thuật toán tìm kiếm, đánh giá, thí nghiệm và kết quả. |
| 3    | `Kakuro as a Constraint Satisfaction Problem` | Mô hình CSP, ràng buộc, thuật toán, heuristic, thí nghiệm và kết quả.        |

Trong phần task của mình, hãy cung cấp:

1. Mô tả ngắn vấn đề và phương pháp **đúng với code hiện tại**, kèm nguồn tham khảo đã sử dụng.
2. Kết quả thực nghiệm đã chạy và kiểm tra: đầu vào, cấu hình, số lần chạy, cách đo, đơn vị và môi trường khi cần. Điền bảng hoặc hình liên quan; không tự đặt số liệu.
3. Nhận xét ngắn về kết quả, giới hạn và các yêu cầu chưa hoàn thành.
4. Công việc cá nhân và mức hoàn thành từ 0% đến 100% để nhóm điền mục `Contributions`.
5. Tự đánh giá task theo rubric của đề, gồm phần đã đạt, chưa đạt và điểm đề xuất để nhóm thống nhất mục `Self-Evaluation`.

Mỗi người cần chuẩn bị giải thích ý tưởng, kết quả và cách code của mình hoạt động khi phỏng vấn. Theo yêu cầu đề, không giải thích rõ và chính xác có thể nhận 0 điểm cho task liên quan.

## Cách sửa và gửi phần của mình

- Thay các đoạn `[placeholder]` thành `your_text` thuộc phần mình; giữ tên section có ý nghĩa và không sửa định dạng trang IEEE.
- Tham chiếu bảng/hình bằng `\ref{...}`, trích dẫn bằng `\cite{...}`. Thêm nguồn thực sự sử dụng vào `thebibliography` theo định dạng IEEE; sắp xếp theo lần xuất hiện trong bài.
- Nếu dùng hình, lưu ảnh vào `docs/figures/`, ghi chú thích và nhắc tới hình trong nội dung. Ví dụ chèn hình đã có trong `report.tex`.
- Gửi người ghép phần LaTeX, ảnh, nguồn tài liệu và dữ liệu/cách chạy dùng để tạo kết quả. Nếu sửa trực tiếp cùng file, thống nhất trước với nhóm hoặc dùng nhánh riêng để tránh ghi đè.
- Không ghi thông tin cá nhân, điểm hoặc tỷ lệ hoàn thành thay người khác khi chưa thống nhất.

Lưu ý: Min-Conflicts không tìm được nghiệm trong giới hạn chạy không chứng minh vô nghiệm. Với Kakuro, chỉ mô tả AC-3 hoặc tính duy nhất nếu code và kết quả thực sự chứng minh được điều đó. Với Tank Battle, chỉ báo cáo tỷ lệ thắng nếu đã có thí nghiệm đo tỷ lệ thắng.

## Ghép và kiểm tra cuối

Người ghép thống nhất `Title`, `Authors` (giảng viên đứng cuối), `Abstract`, `Introduction`, `Contributions`, `Self-Evaluation`, `Conclusion` và `References`. Abstract và Conclusion phải tóm tắt yêu cầu, phương pháp, kết quả thực nghiệm và mức hoàn thành. Kiểm tra placeholder đã được thay, nguồn trích dẫn hợp lệ và điểm khớp rubric.

Từ thư mục gốc dự án, biên dịch hai lần để cập nhật tham chiếu:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=docs docs/report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=docs docs/report.tex
```

Mở `docs/report.pdf`, kiểm tra số trang, hình/bảng, trích dẫn và chữ không bị tràn cột. Cần cài LaTeX có `IEEEtran` trước khi chạy. Mẫu hiện dùng tiếng Anh và `pdflatex`; nếu nhóm muốn viết tiếng Việt, cần thống nhất ngôn ngữ với giảng viên và cấu hình LaTeX hỗ trợ Unicode phù hợp.
