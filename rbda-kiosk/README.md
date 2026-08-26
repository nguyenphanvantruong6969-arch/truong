# Kiosk UI — Phân bổ Câu lạc bộ (RB-DA)

## Cách chạy

```bash
pip install -r requirements.txt
python3 main.py            # dùng app.db mặc định cùng thư mục
python3 main.py /path/to/app.db   # hoặc chỉ định DB khác
```

`rbda_priority_pipeline.py` đã được đặt cùng thư mục với `api.py` —
không cần chỉnh `sys.path.insert` hay copy thêm gì.

## Cấu trúc

```
rbda-kiosk/
  main.py      -> điểm khởi động, tạo cửa sổ pywebview
  api.py       -> lớp PipelineAPI, cầu nối JS <-> rbda_priority_pipeline.py
  rbda_priority_pipeline.py -> thuật toán RB-DA + I/O SQLite (DEFAULT_SCHEMA)
  index.html   -> 5 tab: Vận hành pipeline / Kết quả / Nhập dự phòng /
                  Quản lý club & dự trữ / Chấm điểm (mù)
  style.css    -> giao diện (token: giấy lạnh + ink + vàng đồng)
  app.js       -> logic frontend, gọi window.pywebview.api.*
  tests/       -> bộ test tự động (pytest)
```

## Chạy test tự động

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
python3 -m pytest tests/ -v
```

## Đã test

- **Thuật toán (`tests/test_pipeline_core.py`, 13 test case):**
  `compute_club_priority` (thứ tự 2 tầng + tie-break bằng STB),
  `club_choice_function` (dự trữ được chọn trước, suất dự trữ không
  có ai đủ điều kiện sẽ tự động rơi vào general), `run_rbda` trên các
  kịch bản dựng tay đối chiếu bằng tay (bao gồm 1 kịch bản có dự
  trữ), `validate_data_integrity`, `sanity_check_result`, và 1 test
  tích hợp chạy `run_full_pipeline` trên dữ liệu mẫu 120 học sinh rồi
  xác nhận `sanity_check_result`/`verify_stability` không phát hiện
  vấn đề gì (không có blocking pair — kết quả ổn định đúng lý thuyết
  matching).
- **`api.py` (`tests/test_api.py`, 24 test case):** dashboard, CRUD
  club (kể cả chặn xoá club đang được tham chiếu), tạo/tìm học sinh,
  submit test selection & preferences (thành công + toàn bộ lỗi:
  trùng nguyện vọng, quá 10 club, học sinh không tồn tại, club không
  tồn tại), `run_pipeline` đầy đủ 5 bước (kể cả khoá STB, tái sử dụng
  STB khi chạy lại, vẽ bổ sung STB cho học sinh mới, vẽ lại toàn bộ
  khi `force_redraw_stb=True`, báo lỗi validate đúng cách), chấm điểm
  mù (xác nhận response KHÔNG rò rỉ STB/thứ hạng nguyện vọng), gán
  diện dự trữ hàng loạt, phân trang danh sách học sinh, nhập CSV định
  dạng rộng/dài, và 2 nút mới `reset_student_entry`/`delete_student`
  (xem mục TODO đã xử lý bên dưới). **Tất cả 37 test pass.**
- `app.js`: `node --check` xác nhận không lỗi cú pháp; toàn bộ tên
  hàm `callApi("...")` đối chiếu khớp 1-1 với hàm public trong
  `PipelineAPI`, và toàn bộ id DOM dùng trong `el(...)` đều tồn tại
  trong `index.html`.
- **Giao diện thật trong trình duyệt (Playwright + Chromium, mock
  `window.pywebview.api`):** đã lái thử toàn bộ luồng tab "Nhập dự
  phòng" — tạo học sinh mới, tick chọn club thi, xếp hạng nguyện
  vọng, bấm "Sửa lại từ đầu" (xác nhận 2 bước, xoá đúng cả tick-box
  lẫn danh sách xếp hạng, giữ nguyên học sinh), bấm "Xoá học sinh"
  (xác nhận 2 bước, ẩn khu vực làm việc, xoá đúng học sinh) — chụp
  ảnh màn hình xác nhận bố cục/hành vi đúng như thiết kế.

## CHƯA test được — cần Trường tự chạy trên máy có màn hình

- Cửa sổ pywebview thật đóng gói bằng PyInstaller (kiosk.spec /
  build_windows.bat) — sandbox này không có GTK/QT nên
  `webview.start()` báo lỗi thiếu backend GUI (đã xác minh: lỗi dừng
  đúng ở bước tạo cửa sổ, không phải lỗi code — mọi logic phía sau
  `PipelineAPI` đã được test độc lập với pywebview ở trên).
- Toàn bộ luồng thao tác bằng chuột thật tại kiosk trên phần cứng
  thật (cảm ứng, độ trễ, responsive khi resize cửa sổ thật).

## TODO tiếp theo

- Khi có `02_schema.sql` thật: đối chiếu `DEFAULT_SCHEMA` trong
  `rbda_priority_pipeline.py` — nếu khác, sửa `DEFAULT_SCHEMA` +
  `load_from_sqlite()`/`write_match_results_to_sqlite()`, phần UI
  không cần đổi vì chỉ gọi qua `PipelineAPI`.
- ~~Chưa có nút "xoá học sinh" / "sửa lại từ đầu" ở tab Nhập dự
  phòng~~ — **đã thêm.** `reset_student_entry()` xoá lựa chọn thi +
  nguyện vọng hiện tại (giữ nguyên bản ghi học sinh, dùng để nhập lại
  từ đầu); `delete_student()` xoá hẳn học sinh khỏi hệ thống, CHẶN
  nếu học sinh đã có trong `match_results` của lần chạy pipeline gần
  nhất (để không làm lệch thống kê lấp đầy club / mất dấu kiểm toán —
  phải chạy lại pipeline sau khi xử lý). Cả hai dùng xác nhận 2 bước
  (`armTwoStepConfirm`) giống nút xoá club đã có.
- Chưa có xác thực đăng nhập admin cho tab Pipeline (đúng theo thiết
  kế "offline-first, không có hệ thống đăng nhập" đã chốt trước đó).
