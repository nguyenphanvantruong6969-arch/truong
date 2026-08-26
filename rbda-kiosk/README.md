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
  i18n_errors.py -> catalog lỗi song ngữ (vi/en) dùng ở Python (xem "Song ngữ" bên dưới)
  index.html   -> 5 tab: Vận hành pipeline / Kết quả / Nhập dự phòng /
                  Quản lý club & dự trữ / Chấm điểm (mù)
  style.css    -> giao diện (token: giấy lạnh + ink + vàng đồng)
  i18n.js      -> catalog văn bản song ngữ (vi/en) + hàm dịch dùng ở JS
  app.js       -> logic frontend, gọi window.pywebview.api.*
  tests/       -> bộ test tự động (pytest)
```

## Song ngữ (vi/en)

Toàn bộ giao diện — nhãn tĩnh, toast, thông báo lỗi từ backend — hỗ trợ
2 ngôn ngữ, đổi bằng nút góc trên sidebar (lưu lựa chọn vào
`localStorage`, mặc định tiếng Việt).

Kiến trúc: `api.py` KHÔNG trả về chuỗi tiếng Việt đã format sẵn cho lỗi
nữa — mọi `_fail(...)` trả về `{"code": "...", "params": {...}}` (xem
`i18n_errors.py`). Phía JS (`i18n.js`) có một bản sao **y hệt**
(`ERROR_MESSAGES`) để dịch các code đó sang ngôn ngữ đang chọn mà không
cần gọi lại Python. Văn bản tĩnh trong `index.html` dùng thuộc tính
`data-i18n`/`data-i18n-placeholder`/`data-i18n-html`, áp dụng bằng
`I18N.applyStaticText()`.

Tên club/học sinh (dữ liệu do trường nhập) KHÔNG bị dịch — chỉ chữ
"khung" của app (nhãn nút, tiêu đề, thông báo lỗi/trạng thái) mới song
ngữ.

3 test trong `tests/test_i18n_sync.py` khoá 2 catalog (Python + JS)
luôn khớp nhau tuyệt đối — sửa 1 bên mà quên bên kia sẽ FAIL test ngay,
không đợi phát hiện bằng mắt.

**Lưu ý an toàn đã xử lý:** đổi ngôn ngữ giữa lúc một nút xác nhận
2 bước (`armTwoStepConfirm` — vd "Xoá học sinh") đang ở trạng thái
"đã bấm lần 1" sẽ KHÔNG bị ghi đè nhãn về trạng thái ban đầu (nếu ghi
đè, trạng thái nội bộ "đã bấm lần 1" vẫn còn mà nhãn lại hiện như chưa
bấm — bấm tiếp sẽ xoá NGAY không cảnh báo). Tương tự, thanh xác nhận
"Chạy lại sẽ ghi đè kết quả" (`runConfirmBar`) sẽ tự đóng khi đổi ngôn
ngữ thay vì hiển thị sai ngôn ngữ — người dùng bấm "Chạy pipeline" lại
để có thanh xác nhận mới đúng ngôn ngữ hiện tại.

## Cảnh báo sức khoẻ dữ liệu (pre-flight)

`validate_data_integrity()` chỉ bắt dữ liệu **không hợp lệ**. Nhưng có cả
một nhóm tình huống mà dữ liệu **vẫn hợp lệ**, pipeline **vẫn chạy**, kết
quả **vẫn trông bình thường** — trong khi ai được vào club đã bị đổi bởi
một thiếu sót người vận hành không nhìn thấy. Đã kiểm chứng bằng thực
nghiệm: cả 6 tình huống dưới đây trước đây đều **im lặng hoàn toàn**.

Ví dụ nguy hiểm nhất: giáo viên mới chấm 1/3 danh sách → em được 4.0 điểm
chiếm chắc một suất, còn 2 em chưa chấm bị đẩy xuống Tầng 2 và chỉ được
xét bằng số bốc thăm. Kết quả trông hoàn toàn bình thường.

`get_data_health_report()` rà soát và hiện các cảnh báo này **ngay phía
trên nút "Chạy pipeline"**, phân theo 3 mức (Nghiêm trọng / Cần lưu ý /
Thông tin), sắp xếp nghiêm trọng lên trước:

| # | Tình huống | Hậu quả âm thầm | Mức |
|---|---|---|---|
| 1 | Club có người đăng ký thi nhưng **chưa chấm ai** | Cả club rơi xuống Tầng 2, vòng thi vô nghĩa | Nghiêm trọng |
| 2 | **Chấm dở dang** (mới chấm một phần) | Em chưa chấm bị xếp dưới cả em thấp điểm nhất | Nghiêm trọng |
| 3 | **Thi nhưng không xếp nguyện vọng** club đó | Điểm bị bỏ phí, không bao giờ được xếp vào đó | Nghiêm trọng |
| 4 | Nhãn dự trữ của học sinh **không club nào dùng** (gõ sai) | Học sinh mất quyền ưu tiên ở mọi nơi | Nghiêm trọng |
| 5 | Club có suất dự trữ nhưng **chưa đặt nhãn** | Suất dự trữ âm thầm thành suất phổ thông | Nghiêm trọng |
| 6 | Học sinh **chưa xếp nguyện vọng nào** | Chắc chắn không được xếp vào đâu | Cần lưu ý |
| 7 | Club dành suất cho nhãn **chưa ai mang** | Suất dự trữ không dùng đến | Cần lưu ý |
| 8 | **Tổng chỗ ít hơn số học sinh** | Ít nhất N em chắc chắn không có chỗ | Thông tin |

Đây là **cảnh báo, không phải lỗi** — không chặn chạy pipeline, chỉ bắt
buộc hiện ra để người vận hành tự quyết định.

## Chạy test tự động

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pytest
python3 -m pytest tests/ -v
```

## Đã test

- **Thuật toán (`tests/test_pipeline_core.py`, 14 test case):**
  `compute_club_priority` (thứ tự 2 tầng + tie-break bằng STB),
  `club_choice_function` (dự trữ được chọn trước, suất dự trữ không
  có ai đủ điều kiện sẽ tự động rơi vào general), `run_rbda` trên các
  kịch bản dựng tay đối chiếu bằng tay (bao gồm 1 kịch bản có dự
  trữ), `validate_data_integrity`/`sanity_check_result` (nay trả về
  entry có cấu trúc `{code, params}` — test theo `code`, không theo
  chuỗi con nữa), 1 test xác nhận MỌI entry lỗi thuật toán có thể sinh
  ra đều dịch được sang cả 2 ngôn ngữ (không thiếu key/placeholder), và
  1 test tích hợp chạy `run_full_pipeline` trên dữ liệu mẫu 120 học
  sinh rồi xác nhận `sanity_check_result`/`verify_stability` không
  phát hiện vấn đề gì (không có blocking pair — kết quả ổn định đúng
  lý thuyết matching).
- **`api.py` (`tests/test_api.py`, 25 test case):** dashboard, CRUD
  club (kể cả chặn xoá club đang được tham chiếu), tạo/tìm học sinh,
  submit test selection & preferences (thành công + toàn bộ lỗi:
  trùng nguyện vọng, quá 10 club, học sinh không tồn tại, club không
  tồn tại), `run_pipeline` đầy đủ 5 bước (kể cả khoá STB, tái sử dụng
  STB khi chạy lại, vẽ bổ sung STB cho học sinh mới, vẽ lại toàn bộ
  khi `force_redraw_stb=True`, báo lỗi validate đúng cách — và xác
  nhận step detail/error đều là entry `{code, params}` có cấu trúc,
  không phải chuỗi Việt hoá sẵn), chấm điểm mù (xác nhận response
  KHÔNG rò rỉ STB/thứ hạng nguyện vọng), gán diện dự trữ hàng loạt,
  phân trang danh sách học sinh, nhập CSV định dạng rộng/dài,
  `reset_student_entry`/`delete_student`, và 1 test tĩnh quét toàn bộ
  `api.py`/`rbda_priority_pipeline.py` để chắc chắn mọi `err("code")`
  gọi ra đều có mặt trong catalog với đủ cả 2 ngôn ngữ.
- **Song ngữ (`tests/test_i18n_sync.py`, 3 test case):** catalog lỗi
  JS (`i18n.js`) khớp tuyệt đối với catalog Python (`i18n_errors.py`);
  `UI_STRINGS.vi`/`UI_STRINGS.en` trong `i18n.js` có đúng cùng 1 tập
  key; mọi key `data-i18n`/`data-i18n-placeholder`/`data-i18n-html`
  dùng trong `index.html` đều tồn tại trong `UI_STRINGS`.
- **Cảnh báo dữ liệu (`tests/test_data_health.py`, 14 test case):** mỗi
  trong 8 tình huống ở bảng trên đều được bắt đúng mã cảnh báo, đúng
  mức nghiêm trọng và đúng tham số; kèm các test **đối chứng âm** (dữ
  liệu sạch, DB rỗng, đã chấm đủ, nhãn dự trữ khớp, đủ chỗ → tuyệt đối
  không cảnh báo, tránh "báo động giả"); và 1 test xác nhận mọi cảnh
  báo phát ra đều dịch được sang cả 2 ngôn ngữ, không sót placeholder.
  **Tổng cộng cả 4 file: 62 test, tất cả pass.**
- **Kiểm thử ngẫu nhiên diện rộng:** 400 kịch bản sinh ngẫu nhiên (đủ
  loại quy mô, sức chứa, tỉ lệ dự trữ, tỉ lệ có điểm) — cả 400 đều
  không vi phạm bất biến nào và không tồn tại cặp phá vỡ nào. Ngoài ra
  đã kiểm chứng riêng: cùng seed cho kết quả y hệt (tái lập được), khoá
  STB giữ nguyên kết quả đã công bố kể cả khi chạy lại với seed khác,
  và điểm chấm thắng số bốc thăm đúng như thiết kế (điểm khác nhau →
  seed không đổi kết quả; điểm bằng nhau → seed quyết định).
- `app.js`/`i18n.js`: `node --check` xác nhận không lỗi cú pháp; toàn
  bộ tên hàm `callApi("...")` đối chiếu khớp 1-1 với hàm public trong
  `PipelineAPI`, và toàn bộ id DOM dùng trong `el(...)` đều tồn tại
  trong `index.html`.
- **Giao diện thật trong trình duyệt (Playwright + Chromium chạy
  thẳng vào `PipelineAPI` thật qua một cầu HTTP cục bộ, KHÔNG mock):**
  chạy trọn 1 lượt pipeline thật trên dữ liệu mẫu (45 học sinh/10
  club) — xem cả VI và EN, xác nhận chi tiết từng bước
  (`stb_lottery`, `rbda_cascade`, …) dịch đúng ở cả 2 ngôn ngữ kể cả
  khi dịch LẠI (không gọi lại API) sau khi đổi ngôn ngữ; kích hoạt lỗi
  validate thật (capacity=0) và xác nhận thông báo dịch đúng; lái thử
  toàn bộ luồng tab "Nhập dự phòng" (tạo học sinh, tick chọn club thi,
  xếp hạng nguyện vọng, "Sửa lại từ đầu", "Xoá học sinh") ở cả 2 ngôn
  ngữ. Qua đó phát hiện và sửa 2 lỗi thật liên quan đổi ngôn ngữ giữa
  chừng (xem mục "Song ngữ" ở trên) trước khi merge — không phải chỉ
  kiểm tra bằng mắt tĩnh.

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
