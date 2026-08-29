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
  main.py      -> điểm khởi động, tạo cửa sổ pywebview (KHÔNG BAO GIỜ
                  chết ngầm nếu app.db hỏng — mở recovery.html thay vào)
  api.py       -> lớp PipelineAPI, cầu nối JS <-> rbda_priority_pipeline.py
  rbda_priority_pipeline.py -> thuật toán RB-DA + I/O SQLite (DEFAULT_SCHEMA
                  + connect_db(), pragma bền vững dùng chung mọi kết nối)
  recovery.py  -> lớp RecoveryAPI, chỉ dùng khi app.db hỏng/mất (xem mục
                  "Bền vững dữ liệu & phục hồi sự cố" bên dưới)
  browser_host.py -> chế độ chạy DỰ PHÒNG bằng trình duyệt, tự bật khi
                  pywebview không khởi động được (xem mục cùng tên bên dưới)
  i18n_errors.py -> catalog lỗi song ngữ (vi/en) dùng ở Python (xem "Song ngữ" bên dưới)
  index.html   -> 5 tab: Vận hành pipeline / Kết quả / Nhập dự phòng /
                  Quản lý club & dự trữ / Chấm điểm (mù)
  recovery.html -> màn hình phục hồi độc lập, chỉ mở khi app.db hỏng/mất
  style.css    -> giao diện (token: giấy lạnh + ink + vàng đồng)
  i18n.js      -> catalog văn bản song ngữ (vi/en) + hàm dịch dùng ở JS
  app.js       -> logic frontend, gọi window.pywebview.api.*
  recovery.js  -> logic frontend cho recovery.html, gọi RecoveryAPI
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

## Bền vững dữ liệu & phục hồi sự cố

Xuất phát từ một buổi rà soát thực nghiệm riêng (mô phỏng mất điện giữa
chừng, tệp DB bị cắt cụt/hỏng, ghi đè khi có 2 tiến trình cùng mở app.db)
— đã tìm thấy 4 lỗ hổng thật, cả 4 đều đã vá:

1. **`run_pipeline()` giờ là MỘT giao dịch (transaction) duy nhất.** Vẽ
   STB + khoá STB + ghi `match_results` + ghi `run_meta`/`run_history`
   đều nằm trong cùng 1 connection, chỉ `commit()` MỘT LẦN ở cuối. Nếu
   bất kỳ bước nào ở giữa lỗi — kể cả bị ngắt bằng Ctrl+C/`KeyboardInterrupt`
   — TOÀN BỘ giao dịch rollback, **kể cả số STB vừa vẽ** ("full
   rollback", phương án đã chốt: một crash giữa chừng không bao giờ để
   lại trạng thái "STB đã khoá nhưng không có kết quả nào đi kèm"). Xuất
   CSV chuyển sang xảy ra SAU KHI đã commit thành công — lỗi ghi file
   CSV (hết dung lượng, mất quyền...) không còn có thể kéo DB vào trạng
   thái dở dang.
2. **Tự động sao lưu trước MỖI lần chạy pipeline.** Dùng SQLite Backup
   API (`connection.backup()`, không phải copy file thô — an toàn kể cả
   khi có tiến trình khác đang mở app.db, khác với copy tay có thể chụp
   phải trạng thái nửa-ghi), lưu vào `app.db.bak-<timestamp>` cùng thư
   mục, tự động chỉ giữ lại 10 bản gần nhất.
3. **Không bao giờ chết ngầm nếu app.db hỏng/mất.** Trước đây
   `PipelineAPI(db_path)` (gọi `init_db` bên trong) lỗi thì tiến trình
   thoát với exit code 1 và KHÔNG cửa sổ nào hiện ra — đặc biệt nghiêm
   trọng trên bản build Windows `console=False` (không có terminal nào
   để người vận hành thấy lỗi). Giờ `main.py` bọc bước này trong
   try/except: nếu lỗi, mở `recovery.html` (màn hình riêng, qua
   `RecoveryAPI`) thay vì màn hình chính — hiện lỗi kỹ thuật + danh sách
   bản sao lưu tìm thấy, cho chọn:
   - **Khôi phục từ bản sao lưu gần nhất còn đọc được** — kiểm tra bằng
     `PRAGMA quick_check`; nếu bản mới nhất CŨNG hỏng, tự động lùi sang
     bản kế trước cho tới khi tìm được bản đọc được hoặc hết bản để thử
     (không dừng lại ở bản đầu tiên gặp lỗi).
   - **Bắt đầu với cơ sở dữ liệu mới** — tệp hỏng được ĐỔI TÊN thành
     `app.db.corrupt-<timestamp>` (không xoá, vẫn có thể gửi đi kiểm tra
     sau), rồi tạo `app.db` mới hoàn toàn trống.
   Cả hai thao tác xong đều yêu cầu đóng và mở lại ứng dụng.
4. **Pragma bền vững trên mọi kết nối** (qua `connect_db()` dùng chung
   trong `rbda_priority_pipeline.py`, thay cho gọi `sqlite3.connect()`
   rải rác khắp nơi): `busy_timeout=15000` (15 giây thay vì mặc định 5
   giây — 2 tiến trình cùng mở app.db sẽ CHỜ thay vì báo lỗi "database is
   locked" ngay lập tức) và `synchronous=FULL` (đảm bảo dữ liệu đã thật
   sự nằm trên đĩa sau khi `commit()` trả về, không chỉ trong bộ nhớ
   đệm của hệ điều hành). **Cố tình KHÔNG bật `journal_mode=WAL`** — đã
   thử nghiệm trực tiếp: WAL tạo tệp phụ `app.db-wal` chứa dữ liệu đã
   commit; quy trình sao lưu bằng USB (copy tay file `app.db`) mà không
   biết tới tệp `-wal` sẽ tạo ra bản sao lưu THIẾU dữ liệu mới nhất mà
   không hề báo lỗi — giữ `journal_mode` mặc định (`DELETE`) để file
   `.db` vẫn là bản sao DUY NHẤT cần copy.

## Chế độ dự phòng: cửa sổ ứng dụng riêng dựng bằng trình duyệt

Trên Windows, pywebview **bắt buộc** đi qua `pythonnet` → .NET Framework —
đây là mắt xích hay hỏng nhất khi đóng gói bằng PyInstaller. Đã gặp lỗi
thật trên máy người dùng khi chạy bản `.exe`:

```
RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize
from ...\_internal\pythonnet\runtime\Python.Runtime.dll
```

(chữ "from" cho thấy tệp DLL **có mặt** — .NET tìm thấy nhưng từ chối nạp;
nguyên nhân nằm ngoài tầm kiểm soát của mã nguồn). Trước đây lỗi này làm
cả tiến trình chết kèm hộp thoại khó hiểu, app hoàn toàn không dùng được.

Giờ `main.py` thử theo thứ tự:

1. **Cửa sổ pywebview** — ưu tiên, đúng trải nghiệm kiosk (cửa sổ riêng).
2. **Nếu pywebview hỏng vì bất kỳ lý do gì** → tự động chuyển sang
   `browser_host.py`: dựng một máy chủ HTTP cục bộ rồi mở **một CỬA SỔ
   ỨNG DỤNG RIÊNG**. Chế độ này **không dùng pythonnet/.NET/thư viện GUI
   nào cả** — chỉ thư viện chuẩn của Python + trình duyệt vốn có sẵn trên
   mọi máy Windows — nên gần như không thể hỏng vì lý do đóng gói.

### Vì sao vẫn là "ứng dụng riêng", không phải tab trình duyệt

Mọi trình duyệt nhân Chromium (Edge, Chrome, Brave, Chromium) đều hiểu cờ
`--app=<url>`: mở **một cửa sổ riêng, không thanh địa chỉ, không thanh
tab, không nút Back/Refresh**, có mục riêng trên thanh tác vụ. Nhìn và
dùng y như một ứng dụng desktop.

Điều này quan trọng với máy kiosk đặt ở trường: có thanh địa chỉ nghĩa là
học sinh gõ được sang trang khác, đóng nhầm tab của app, hoặc nhìn thấy cả
token trong URL.

`browser_host.find_app_window_browser()` tìm theo thứ tự: biến môi trường
`RBDA_BROWSER` (nếu người vận hành muốn chỉ định thẳng) → đường dẫn cài
đặt tiêu chuẩn của **Edge** rồi Chrome/Brave trên Windows → cuối cùng mới
tra `PATH`. **Windows 10/11 luôn có sẵn Edge**, nên trên máy trường gần
như chắc chắn tìm được.

Cửa sổ chạy bằng **hồ sơ trình duyệt riêng** (`--user-data-dir` trong thư
mục tạm): không dính extension, lịch sử, hay hộp thoại "khôi phục tab" của
người dùng. Mất hồ sơ đó cũng không sao — dữ liệu thật nằm hết trong
`app.db`.

Firefox không có cờ tương đương (`-kiosk` chiếm trọn màn hình, không có
nút đóng — quá tay cho phòng máy dùng chung), nên chỉ tìm nhóm Chromium.
Máy nào không có trình duyệt Chromium nào thì mới đành mở tab thường —
vẫn dùng được đủ tính năng, chỉ kém gọn.

**Toàn bộ tính năng giữ nguyên**, và `app.js`/`recovery.js` **không phải
sửa một dòng nào**: giao diện vẫn gọi backend qua đúng
`window.pywebview.api.<tên_hàm>(...)` như cũ, còn `browser_host` chèn sẵn
một đoạn JS dựng `window.pywebview.api` giả lập (bằng Proxy) vào mỗi trang
HTML nó phục vụ — mỗi lời gọi biến thành một POST tới `/__api__/<tên_hàm>`.

An toàn (đây là máy chứa dữ liệu học sinh):

- Chỉ lắng nghe trên `127.0.0.1` — không ra ngoài mạng LAN.
- Mọi lời gọi API phải kèm **token ngẫu nhiên** sinh lúc khởi động, để một
  trang web bất kỳ đang mở trong cùng trình duyệt không thể tự gọi vào.
- **Không cho gọi phương thức nội bộ** (tên bắt đầu bằng `_`, ví dụ
  `_backup_db`) qua HTTP.
- Endpoint tắt máy chủ (`/__closed__`) cũng **bắt buộc có token**, để một
  trang web khác dò trúng cổng không tắt được app đang chạy dở.

Tắt đúng lúc — không tắt nhầm khi thu nhỏ:

- Đóng cửa sổ → trang gửi `navigator.sendBeacon("/__closed__")` trong sự
  kiện `pagehide`, máy chủ **tắt ngay** (đo thực tế: ~3 giây).
- Ngoài ra trang vẫn gửi tín hiệu "còn mở" mỗi 3 giây; quá **120 giây**
  không thấy tín hiệu thì tiến trình tự tắt — lưới an toàn cho trường hợp
  trình duyệt bị kill cứng, không kịp gửi beacon.
- **Vì sao 120 giây chứ không phải 25:** trình duyệt bóp thắt (throttle)
  `setInterval` của trang đang bị ẩn, cửa sổ thu nhỏ lâu thì tín hiệu tụt
  xuống khoảng 1 lần/phút. Với ngưỡng 25 giây cũ, người vận hành chỉ cần
  thu nhỏ cửa sổ đi làm việc khác là **app tự tắt giữa chừng** — một ứng
  dụng thật không hành xử như vậy.

## Nhập dữ liệu bằng CSV

Thư mục **`mau_csv/`** chứa 4 file mẫu chạy được ngay và
**`mau_csv/HUONG_DAN_CSV.md`** mô tả đầy đủ định dạng:

| File mẫu | Loại | Dạng |
|---|---|---|
| `01_chon_club_thi_dang_rong.csv` | Chọn club muốn thi (Bước 1) | rộng — 1 dòng/học sinh |
| `02_chon_club_thi_dang_dai.csv` | Chọn club muốn thi (Bước 1) | dài — 1 dòng/lựa chọn |
| `03_nguyen_vong_dang_rong.csv` | Xếp hạng nguyện vọng (Bước 2) | rộng |
| `04_nguyen_vong_dang_dai.csv` | Xếp hạng nguyện vọng (Bước 2) | dài |

Phần mềm tự nhận diện dạng file và dấu phân cách (`,` `;` Tab), nên người
dùng không phải chọn gì.

**Hai điểm dễ sai nhất, đã ghi rõ trong hướng dẫn:**

1. **`club_id` phải được tạo trước khi nhập.** Học sinh có bất kỳ `club_id`
   nào chưa tồn tại sẽ bị **bỏ qua toàn bộ** (kèm cảnh báo) — phần mềm
   không nhập một nửa.
2. **CSV không gán được `reserve_group`.** Học sinh tạo bằng CSV có nhóm dự
   trữ rỗng, phải vào màn hình *04 Quản lý club & dự trữ* gán riêng. Quên
   bước này thì cơ chế dự trữ của RB-DA không có tác dụng, mà pipeline vẫn
   chạy bình thường và **không báo lỗi**.

Mọi quy tắc trong `HUONG_DAN_CSV.md` đều được khoá bằng test
(`tests/test_csv_mau.py`) — tài liệu và code không thể lệch nhau mà không
làm đỏ test.

**Về Excel:** file lưu bằng *CSV UTF-8* có ký tự BOM vô hình ở đầu. Trước
đây chính ký tự đó khiến một file hoàn toàn đúng vẫn báo "thiếu cột
`student_id`"; nay đã được xử lý.

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
- **Bền vững dữ liệu (`tests/test_data_durability.py`, 15 test case):**
  Nhóm A (nguyên tử) — `run_pipeline` tự sao lưu trước khi chạy, giữ
  đúng tối đa 10 bản; một `Exception` thường HAY một `KeyboardInterrupt`
  (không kế thừa `Exception`) nổ ra giữa chừng sau khi đã vẽ STB đều
  khiến state DB (khoá STB, `match_results`, `run_history`, số STB từng
  học sinh) giữ NGUYÊN Y HỆT trạng thái trước khi chạy — full rollback
  thật sự, không chỉ ở phần ghi kết quả; `KeyboardInterrupt` phải được
  ném lại (không bị nuốt thành lỗi nghiệp vụ thường); một lỗi sanity/
  stability (không phải exception) cũng rollback đúng cách; và app vẫn
  chạy lại bình thường ngay sau một lần crash. Nhóm B (tệp hỏng/mất) —
  tệp rác hoàn toàn hoặc bị cắt cụt khiến `PipelineAPI` báo lỗi rõ ràng
  (không phải im lặng); `RecoveryAPI` báo đúng khi không có bản sao lưu
  nào; "bắt đầu mới" đổi tên tệp hỏng (không xoá) và tạo được DB hoạt
  động lại; khôi phục từ bản sao lưu khôi phục ĐÚNG lại toàn bộ lịch sử
  chạy; và — kịch bản khó nhất — nếu bản sao lưu MỚI NHẤT cũng hỏng,
  quy trình tự động lùi sang bản kế trước còn đọc được thay vì dừng lại
  ở lỗi đầu tiên, báo đúng cả tên bản đã dùng lẫn số bản đã bỏ qua.
- **Chế độ trình duyệt (`tests/test_browser_host.py`, 21 test case):** lời
  gọi qua HTTP đi ĐÚNG vào `PipelineAPI` thật (tạo học sinh qua HTTP rồi
  đọc lại bằng đối tượng Python thấy đúng dữ liệu, không phải backend
  giả); thiếu token hoặc sai token → 403; phương thức nội bộ (`_backup_db`)
  → 404, không lộ ra ngoài; phương thức không tồn tại → 404 chứ không làm
  sập máy chủ; lỗi bên trong backend trả về `{ok: false}` để UI hiện được;
  shim `window.pywebview` được chèn vào CẢ `index.html` lẫn `recovery.html`
  và chèn ĐÚNG trước `</head>` (nếu chèn sau, `app.js` sẽ chạy trước khi
  cầu nối tồn tại); `app.js`/`style.css` được phục vụ nguyên văn không bị
  sửa; và máy chủ chỉ bind vào `127.0.0.1`.
  **Tổng cộng cả 6 file: 88 test, tất cả pass.**
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
- **`recovery.html` (Playwright, `window.pywebview.api` giả lập đúng
  hợp đồng của `RecoveryAPI`):** hiện đúng lỗi kỹ thuật + bảng bản sao
  lưu ở cả VI/EN; bấm "Khôi phục" và "Bắt đầu mới" (qua xác nhận 2
  bước) đều hiện đúng thông báo kết quả dịch đúng ngôn ngữ, không sót
  placeholder, không lỗi console. Qua đó phát hiện và sửa 1 lỗi thật:
  nút đổi ngôn ngữ dùng nhầm class `.lang-toggle` (thiết kế cho nền tối
  của sidebar) trên nền trắng của trang phục hồi, khiến chữ trắng-trên-
  trắng vô hình — đã tách riêng class `.lang-toggle-light`.
- **Chế độ trình duyệt chạy thật (Playwright + Chromium, backend là
  `PipelineAPI` THẬT qua `browser_host`, dữ liệu mẫu 45 học sinh/10
  club):** mở `index.html` qua máy chủ cục bộ, xác nhận cầu nối
  `window.pywebview` được dựng đúng, sidebar hiện "Đã kết nối app.db",
  4 ô thống kê nạp đúng số (45/10/45/0), bảng cảnh báo sức khoẻ dữ liệu
  hiện 10 cảnh báo; bấm "Chạy pipeline" và chạy TRỌN 5 bước thật qua cầu
  HTTP (vẽ + khoá STB cho 45 học sinh, RB-DA 1 vòng, ghi DB, xuất CSV),
  toast báo "45/45 học sinh đã xếp club"; sang tab Kết quả thấy đúng 45
  dòng đọc ngược từ DB; đổi sang tiếng Anh vẫn hoạt động. Không lỗi
  console. Tức là chế độ dự phòng **không phải bản rút gọn** — nó chạy
  đầy đủ y hệt bản pywebview.

## CHƯA test được — cần Trường tự chạy trên máy có màn hình

- Cửa sổ pywebview thật đóng gói bằng PyInstaller (kiosk.spec /
  build_windows.bat) — sandbox này không có GTK/QT nên
  `webview.start()` báo lỗi thiếu backend GUI (đã xác minh: lỗi dừng
  đúng ở bước tạo cửa sổ, không phải lỗi code — mọi logic phía sau
  `PipelineAPI`/`RecoveryAPI` đã được test độc lập với pywebview ở
  trên, kể cả nhánh main.py mở `recovery.html` khi khởi tạo lỗi).
  **Lưu ý:** kể từ khi có chế độ dự phòng bằng trình duyệt, đây không
  còn là rủi ro chặn đường nữa — pywebview hỏng thì app tự chuyển sang
  trình duyệt, và nhánh đó ĐÃ được chạy thật đầy đủ (xem mục trên).
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
