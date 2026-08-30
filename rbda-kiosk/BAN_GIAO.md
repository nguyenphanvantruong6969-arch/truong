# BÀN GIAO NGỮ CẢNH — Dự án RB-DA

> **Đọc file này đầu tiên khi bắt đầu phiên làm việc mới.**
> Cập nhật lần cuối: 30/08/2026 · 234 test pass

---

## 1. Dự án là gì

Phần mềm kiosk **phân bổ học sinh vào Câu lạc bộ** cho một trường THPT, dùng thuật toán
**Reserve-Based Deferred Acceptance (RB-DA)** — họ Gale–Shapley, có dự trữ mềm
(soft reserves, Kominers & Sönmez 2016) và Single Tie-Breaking (STB).

Đây là **đề tài dự thi nghiên cứu khoa học cấp Sở GD&ĐT**, không phải phần mềm thương mại.
Điều này quan trọng: xem mục 6 về quy định sử dụng AI.

**Kiến trúc:** ứng dụng desktop offline — pywebview (Python) + HTML/CSS/JS thuần, dữ liệu
trong SQLite một file (`app.db`). Không có server, không đăng nhập (chốt từ đầu: offline-first).

---

## 2. Trạng thái hiện tại

| | |
|---|---|
| Repo | `nguyenphanvantruong6969-arch/truong`, thư mục `rbda-kiosk/` |
| Nhánh | `claude/project-testing-development-zf9ajs` |
| Test | **234 test, tất cả pass** (`./.venv/bin/python -m pytest -q`) |
| Bản `.exe` | Build qua GitHub Actions (workflow `build-windows-exe.yml`, chạy tay) |

**Chạy thử:**
```bash
cd rbda-kiosk
python3 -m venv .venv                        # XEM LƯU Ý bên dưới
./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/python -m pytest -q              # chạy test
./.venv/bin/python main.py                   # chạy app
```

> **LƯU Ý cho phiên làm việc mới:** `.venv/` nằm trong `.gitignore` nên KHÔNG
> theo repo. Máy chạy phiên Claude là container mới, clone lại từ đầu mỗi lần
> — nên **luôn phải dựng lại `.venv` trước khi chạy test**. Đừng tưởng dự án
> hỏng khi thấy `./.venv/bin/python: No such file or directory`.

---

## 3. Bản đồ mã nguồn

### Học sinh tự viết (bản gốc upload 26/08/2026)
- `rbda_priority_pipeline.py` — **thuật toán lõi**. `DEFAULT_SCHEMA` trong file này là nguồn
  sự thật duy nhất cho schema DB (không có `02_schema.sql` riêng).
- `api.py` — lớp `PipelineAPI`, cầu nối JS ↔ Python. Mọi hàm trả `{ok, data, errors}`.
- `main.py`, `index.html`, `style.css`, `app.js`, `kiosk.spec`
- `ky_va_tin_cay.ps1` + `HUONG_DAN_CAI_DAT.md` — xử lý cảnh báo chữ ký Windows

### AI viết mới (đã trích dẫn đầy đủ trong nhật ký AI)
- `i18n.js` (830) + `i18n_errors.py` (415) — từ điển song ngữ vi/en, **phải luôn khớp nhau**
  (test `test_i18n_sync.py` bắt buộc)
- `recovery.py` / `recovery.html` / `recovery.js` — màn hình phục hồi khi `app.db` hỏng
- `browser_host.py` (237) — chế độ chạy dự phòng bằng trình duyệt
- `tests/` — 15 file test, 234 test case (có 1 file chạy giao diện thật bằng Playwright)
- `mau_csv/` — 5 file CSV mẫu + 3 file Excel mẫu + `HUONG_DAN_CSV.md`
  + `tao_mau_excel.py` (sinh lại bộ Excel từ bộ CSV)
- `du_lieu_test/` — 4 file Excel **dữ liệu mô phỏng** ở quy mô thật (120 học sinh,
  10 CLB) + 1 file cố ý sai 5 chỗ, kèm `tao_du_lieu_test.py` (seed = 2026) và
  `README.md` ghi rõ kết quả đúng phải ra thế nào, kèm `NHAP_TAY.md` — kịch bản
  gõ tay 8 học sinh / 3 CLB cho các màn hình mà đường nạp tệp không chạm tới

---

## 4. Quyết định đã chốt — ĐỪNG tự ý đảo ngược

1. **Không bật WAL mode cho SQLite.** Đã thí nghiệm và xác nhận: WAL tạo file phụ `app.db-wal`,
   khiến quy trình sao lưu bằng USB (copy tay file `.db`) tạo ra bản sao **thiếu dữ liệu mới nhất
   mà không báo lỗi**. Giữ `journal_mode=DELETE`. Chỉ dùng `synchronous=FULL` + `busy_timeout=15000`.

2. **`run_pipeline()` là một giao dịch duy nhất, huỷ toàn bộ khi lỗi** (kể cả số STB vừa vẽ).
   Đã chốt phương án này thay vì "giữ lại số bốc thăm".

3. **pywebview là chính, trình duyệt là dự phòng.** Không bỏ pywebview.
   Lý do có chế độ dự phòng: xem mục 5.

4. **Số bốc thăm STB khoá sau lần chạy đầu.** Chạy lại chỉ vẽ bổ sung cho học sinh mới.
   Vẽ lại toàn bộ cần xác nhận 2 bước trên UI.

5. **Không thêm hệ thống đăng nhập.** Đúng thiết kế "offline-first" đã chốt.

6. **Chế độ dự phòng mở CỬA SỔ ỨNG DỤNG RIÊNG, không phải tab trình duyệt.**
   Dùng cờ `--app=<url>` của trình duyệt nhân Chromium (Edge có sẵn trên mọi
   máy Windows 10/11) → cửa sổ riêng, không thanh địa chỉ, không tab. Đã kiểm
   chứng chạy thật bằng Chromium + Xvfb trong sandbox. Không dùng Firefox vì
   nó không có cờ tương đương. Nếu máy không có trình duyệt Chromium nào mới
   quay về mở tab thường.

7. **KHÔNG bao giờ đoán loại file CSV khi dòng tiêu đề không đủ kết luận.**
   Giao diện cũ có hai ô nạp file và bắt người dùng tự chọn; chọn nhầm thì dữ
   liệu vào SAI BẢNG mà vẫn báo "thành công" (file nguyện vọng dạng dài khớp
   đủ cột của ô chọn-CLB-thi). Nay `detect_csv_kind()` tự nhận diện, và khi
   bộ cột là `student_id, club_id` không kèm `rank` — hợp với cả hai loại —
   thì DỪNG LẠI hỏi người dùng. Đoán bừa ở đây là dựng lại đúng cái bug đó.

8. **Thứ tự nhập bắt buộc: CLB trước, học sinh sau** (`THU_TU_NHAP` trong
   `app.js`). Học sinh tham chiếu `club_id`; nạp ngược thứ tự thì CẢ học sinh
   bị bỏ qua. Giao diện tự sắp xếp nên người dùng thả file thứ tự nào cũng
   được, nhưng đừng bỏ cơ chế sắp xếp này đi.

9. **File xuất kết quả đặt CẠNH `app.db`, không dùng đường dẫn tương đối.**
   Đường dẫn tương đối rơi vào thư mục làm việc của tiến trình — trên máy
   Windows chạy `.exe` qua shortcut, thư mục đó có thể là bất kỳ đâu và
   người dùng không tìm ra file. `export_csv` luôn trả về đường dẫn ĐẦY ĐỦ
   để giao diện hiện đúng chỗ. Cũng phải giữ `utf-8-sig` (BOM) khi ghi,
   nếu không Excel hỏng font tên tiếng Việt.

10. **`openpyxl` đọc thẳng .xlsx — KHÔNG bỏ đi.** Microsoft Forms xuất ra
   `.xlsx`; bắt người dùng tự Save As CSV là bước thừa và là chỗ hỏng dấu
   tiếng Việt nhiều nhất. Ba chỗ .xlsx khác CSV đã xử lý, đừng làm hỏng:
   số thực `20.0` phải đưa về `20` (không thì `int()` ném lỗi và **cả dòng
   CLB bị bỏ qua**), ô trống `None` phải về chuỗi rỗng, và lấy **sheet đầu
   tiên** chứ không phải sheet đang active. `openpyxl` là Python thuần,
   không dính .NET như pythonnet nên không thêm rủi ro đóng gói.

11. **`reserve_group` của học sinh: ô có giá trị GHI ĐÈ, ô trống GIỮ NGUYÊN.**
   Điền được thẳng trong cả hai file học sinh. Ô trống tuyệt đối không được
   xoá nhóm đã gán — file nhập lại mà thiếu giá trị sẽ làm mất dữ liệu.

12. **Mọi nhãn `reserve_group` phải đi qua `chuan_hoa_nhom_du_tru()` TRƯỚC
   khi ghi.** Nhãn gõ ở hai nơi (file CLB và file học sinh) và phải khớp thì
   dự trữ mới chạy; trước đây `chinh_sach` vs `Chính sách` là hai nhóm khác
   nhau và học sinh diện ưu tiên vào theo diện `general`, pipeline vẫn chạy
   hết không báo lỗi. Đã áp dụng ở 5 đường ghi: `create_or_update_club`,
   `import_clubs_csv`, `_ghi_nhom_du_tru` (2 đường CSV học sinh),
   `set_student_reserve_group`, `bulk_set_reserve_group`. Thêm đường ghi mới
   thì PHẢI gọi hàm này.

   Chuẩn hoá lúc GHI chứ không phải lúc SO SÁNH là chủ ý —
   `rbda_priority_pipeline.py` vẫn so khớp chuỗi chính xác, phần thuật toán
   không bị đụng tới.

   Dữ liệu nhập từ TRƯỚC bản này có thể còn nhãn chưa chuẩn; nhập lại file
   CLB và file học sinh là tự quy về mã chuẩn.

13. **`student_id` PHÂN BIỆT hoa/thường, `club_id` thì KHÔNG.** Có chủ ý:
   `club_id` có danh sách gốc trong bảng `clubs` để đối chiếu nên khớp
   hoa/thường an toàn (`_khop_club_id`, thử khớp chính xác TRƯỚC rồi mới bỏ
   qua hoa/thường — trường tạo cả `clb_a` lẫn `CLB_A` thì mã chính xác vẫn
   thắng). `student_id` không có gì để đối chiếu, nên chỉ CẢNH BÁO khi hai mã
   khác nhau mỗi hoa/thường, tuyệt đối KHÔNG tự gộp: gộp nhầm hai em có thật
   là hỏng nặng hơn nhiều so với để người nhập tự sửa.

14. **Ngưỡng tự tắt là 120 giây, KHÔNG được hạ xuống.** Trình duyệt bóp thắt
   `setInterval` của trang bị ẩn xuống ~1 lần/phút; ngưỡng 25 giây cũ khiến
   app tự tắt khi người vận hành chỉ thu nhỏ cửa sổ. Việc tắt nhanh khi đóng
   thật do `sendBeacon` trong `pagehide` lo (đo thực tế ~3 giây), không phải
   do ngưỡng này.

---

## 5. Vấn đề chưa giải quyết

**Bản `.exe` Windows lỗi khi khởi động:**
```
RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize
from ...\_internal\pythonnet\runtime\Python.Runtime.dll
```

- **Đã loại trừ:** UPX (chưa bao giờ được dùng — máy build GitHub không cài UPX);
  thiếu file pythonnet (hook chính thức của pythonnet đã chạy sẵn ở bản lỗi).
- **Bằng chứng quan trọng:** thông báo ghi *"from &lt;đường dẫn&gt;"* → file DLL **có mặt**,
  .NET tìm thấy nhưng từ chối nạp. Nên hướng "gom thêm file" là **sai hướng**.
- **Đã xử lý:** chế độ dự phòng giờ mở **cửa sổ ứng dụng riêng** (`--app=`),
  nên kể cả khi pywebview vẫn hỏng, người dùng vẫn thấy một ứng dụng riêng
  chứ không phải tab trình duyệt. Đã kiểm chứng chạy thật (xem mục 4.6).
- **Đã đọc log build run `33124799256`** (commit `b39e426`): build THÀNH CÔNG,
  không lỗi. Phiên bản thực tế được cài: `pythonnet 3.1.0`, `clr_loader 0.3.1`,
  `pywebview 6.2.1`, PyInstaller 6.22.2, Python 3.11.9. Hook chính thức
  `pythonnet/_pyinstaller/hook-clr.py` VÀ `hook-clr_loader.py` đều đã chạy.
  Nghĩa là lỗi hoàn toàn nằm ở lúc CHẠY, không phải lúc đóng gói.
- **Đã truy được chỗ ném lỗi:** `clr_loader/netfx.py` dòng 46-49 — `netfx`
  nghĩa là .NET **Framework** (không phải .NET Core). Trên Windows,
  `pythonnet/__init__.py` mặc định chọn `netfx`. Lỗi xảy ra khi
  `pyclr_get_function` trả NULL, tức .NET Framework nạp được DLL nhưng không
  resolve được hàm `Python.Runtime.Loader.Initialize` trong đó.
- **CHƯA KIỂM CHỨNG ĐƯỢC:** vì sao .NET Framework từ chối. Sandbox là Linux,
  không có .NET Framework để thử. Mọi giả thuyết về nguyên nhân gốc lúc này
  đều là PHỎNG ĐOÁN — đúng thứ đã sai 2 lần trước.
- **Phương án chưa thử:** khoá phiên bản cụ thể của `pythonnet`/`clr_loader`;
  hoặc đặt `PYTHONNET_RUNTIME=coreclr` (nhưng đòi máy cài sẵn .NET Core).

**Việc tiện lợi CÒN LẠI đã khảo sát nhưng chưa làm** (xem lại nếu học sinh hỏi):
- ~~Club phải tạo tay từng cái~~ — ĐÃ XONG: `import_clubs_csv` +
  `mau_csv/05_danh_sach_club.csv`.
- ~~`reserve_group` của HỌC SINH~~ — ĐÃ XONG: cột `reserve_group` trong cả
  hai file học sinh (xem mục 4.11).
- ~~Phải tự chuyển Excel sang CSV~~ — ĐÃ XONG: `xlsx_to_csv_text` đọc thẳng
  `.xlsx`, kèm 3 file Excel mẫu có sheet hướng dẫn.
- ~~Lệch tên nhóm dự trữ~~ — ĐÃ XONG: chuẩn hoá nhãn (mục 4.12) + cảnh báo
  `csv_reserve_group_unknown` hiện NGAY lúc nhập, kèm gợi ý nhóm gần giống
  nhất (`difflib.get_close_matches`). Mục Cảnh báo dữ liệu vốn ĐÃ bắt được
  ca này từ trước (mục 4 và 6 của `get_data_health_report`), nhưng nằm ở
  panel khác nên rất dễ lướt qua.
- **Chưa có nút "Sao lưu ngay" / "Khôi phục"** trong app thường; hiện chỉ
  tự sao lưu trước mỗi lần chạy pipeline, còn khôi phục thì chỉ xuất hiện
  ở màn hình recovery — tức là SAU KHI DB đã hỏng. Quy trình sao lưu đã
  chốt là copy tay file `.db` qua USB (mục 4.1), nên một nút "Xuất bản sao
  lưu ra USB" sẽ khớp đúng quy trình đó.

**Đã soát thủ công luồng nạp (29/08), các ca CÒN LẠI chưa xử lý:**
- ~~Excel làm mất số 0 đứng đầu mã học sinh~~ — ĐÃ CÓ CẢNH BÁO
  (`_soat_ma_nghi_bi_cat`): mã toàn chữ số ngắn hơn độ dài phổ biến trong cùng
  file thì báo `csv_student_id_maybe_truncated`. Ba điều kiện chống nhiễu: chỉ
  xét mã toàn số, cần ≥3 mã như vậy, và mã ngắn phải là thiểu số. KHÔNG tự thêm
  số 0 — phần mềm không biết mã gốc dài bao nhiêu, đoán thêm là bịa dữ liệu.
- **File .xlsx chứa CÔNG THỨC chưa được Excel tính sẵn** đọc ra ô rỗng
  (`data_only=True` lấy giá trị đã lưu, file do openpyxl tạo thì không có).
  File Excel thật do Excel lưu luôn có giá trị nên thực tế hiếm gặp; dòng
  hỏng vẫn bị bỏ qua kèm cảnh báo `csv_club_row_invalid`.

**Cảnh báo chữ ký số của Windows (30/08):** bản `.exe` không có chữ ký thương mại
nên Windows SmartScreen cảnh báo "nhà phát hành không xác định". Đây KHÔNG phải lỗi
phần mềm — mọi ứng dụng không mua chứng chỉ đều bị. Chứng chỉ OV giá 200–400 USD/năm
mà SmartScreen VẪN cảnh báo tới khi đủ lượt tải; chỉ EV (400–1000 USD/năm, kèm USB
token) mới hết ngay → ngoài tầm với đề tài học sinh.

Đã làm hai đường đi được, ghi trong `HUONG_DAN_CAI_DAT.md`:
- **Bấm qua cảnh báo** (More info → Run anyway) — mặc định, không cần quyền gì, và
  Windows nhớ lựa chọn nên chỉ hiện lần đầu trên mỗi máy.
- **`ky_va_tin_cay.ps1`** — tạo chứng chỉ tự ký, cài vào kho tin cậy, ký `.exe`.
  Hết cảnh báo hoàn toàn NHƯNG chỉ trên máy đã chạy script (cần Administrator).

### Bộ dữ liệu chạy thử (`du_lieu_test/`)

Đã chạy trọn quy trình với bộ này trong sandbox: nạp 3 file Excel → chấm điểm 356
lượt → `run_pipeline(seed=42)` → xuất kết quả. Ra **118/120 em được xếp**, 2 em vào
`_chua_duoc_xep.csv`, 11 file theo CLB. File `TEST_04_CO_LOI_CO_Y.xlsx` cho ra đủ
**5 cảnh báo** đã hứa trong sheet Ghi chú.

`NHAP_TAY.md` hứa một bảng kết quả cụ thể và bảo người dùng "ra khác là phần mềm
sai". Lời hứa đó được canh bằng `tests/test_kich_ban_nhap_tay.py` (8 test) — không
có test canh thì một thay đổi thuật toán sẽ âm thầm làm tài liệu nói dối. Kịch bản
cố ý không có hai em bằng điểm trong cùng CLB, nên STB không được dùng tới: đã chạy
với 5 seed khác nhau, kết quả giống hệt nhau.

Chính bộ này lộ ra lỗi thứ mười: `_soat_ma_trung_hoa_thuong` chỉ đối chiếu mã trong
file với mã **đã có trong CSDL**, nên hai cách viết `HS201`/`hs201` nằm trong **cùng
một file** (cả hai đều mới) thì lọt hoàn toàn. Đã sửa và có test riêng.

### ✅ ĐÃ CHẠY ĐƯỢC TRÊN MÁY WINDOWS THẬT (30/08) — học sinh xác nhận

Ba câu hỏi chặn cả tuần đã có câu trả lời, học sinh tự quan sát và báo lại:

| Câu hỏi | Kết quả |
|---|---|
| Cửa sổ riêng hay tab trình duyệt? | **Cửa sổ ứng dụng riêng** |
| Có mục riêng trên thanh tác vụ? | **Có** |
| Thu nhỏ 3–5 phút rồi mở lại còn sống? | **Còn sống** |

Học sinh cũng đã nạp thành công cả 4 tệp Excel trong `du_lieu_test/` và gửi ảnh
màn hình. **Mười con số ứng viên mỗi CLB (31 · 35 · 37 · 36 · 43 · 38 · 28 · 34 ·
31 · 43) khớp từng cái với kết quả đo trong sandbox** — đường đọc Excel → nhận
diện → ghi CSDL cho kết quả giống nhau trên hai máy khác nhau.

Học sinh báo **không gặp lỗi nào**. 11 cảnh báo trên màn hình là phần mềm chạy
ĐÚNG: 10 cảnh báo "chưa chấm điểm" (đo được: chấm xong thì 11 → 1) và 1 cảnh báo
nhãn `chinh_sac` — chính là lỗi cố ý trong `TEST_04`, bị bắt lần thứ hai bởi một
cơ chế khác với lúc nhập tệp.

**CÒN MƠ HỒ — đừng ghi vào báo cáo trước khi làm rõ:** "cửa sổ ứng dụng riêng"
KHÔNG phân biệt được hai đường. Cả pywebview lẫn chế độ dự phòng `--app=` đều cho
ra cửa sổ không thanh địa chỉ, không thanh tab, có mục riêng trên thanh tác vụ.
Nên **chưa kết luận được lỗi pythonnet đã hết hay chỉ là đường dự phòng đang gánh**.
Muốn biết: mở Task Manager, nếu thấy tiến trình `msedge.exe` (hoặc `chrome.exe`)
xuất hiện lúc mở app thì đó là đường dự phòng.

**Chưa kiểm chứng trên máy thật:** các bước SAU khi nạp dữ liệu (chấm điểm, chạy
phân bổ, xuất kết quả), thao tác chuột/cảm ứng trên
máy kiosk thật, và **toàn bộ `ky_va_tin_cay.ps1`** — sandbox là Linux, không có
`signtool`, không có kho chứng chỉ Windows. Đã kiểm được cú pháp PowerShell (parse
sạch, 988 token) và logic tìm file, nhưng các lệnh `New-SelfSignedCertificate`,
`Import-Certificate`, `signtool sign` thì CHƯA CHẠY THẬT lần nào.

---

## 6. Quy định sử dụng AI của Sở GD&ĐT — BẮT BUỘC ĐỌC

Đề tài này chịu ràng buộc của **Phụ lục 1 (Bảng Quy Định Sử Dụng AI)** và
**Phụ lục 2 (Sổ Nhật Ký Nghiên Cứu)**.

**Được phép kèm điều kiện:** AI viết mã nguồn — nhưng **phải trích dẫn rõ code nào do AI tạo
+ lưu nhật ký câu lệnh**. Đã có: `Nhat_Ky_AI_RB-DA.pdf` (artifact
`https://claude.ai/code/artifact/1369e5c3-3d9f-4d8f-8c00-0328bc1b5131`).

**KHÔNG bao giờ được phép** — AI tuyệt đối không làm:
- Viết bản thảo kế hoạch nghiên cứu, tóm tắt (abstract), bài báo, poster
- Viết bất kỳ phần nào của bài nghiên cứu để nộp dưới tên học sinh
- **Viết phần Kết luận hoặc Hướng phát triển tương lai của bài nghiên cứu**
- Bổ sung luận điểm mới vào bài đã viết
- Thu thập dữ liệu nghiên cứu, tìm trích dẫn chứng minh, tạo danh mục tài liệu tham khảo

**Điều kiện phải nhắc học sinh mỗi khi liên quan:**
- Sơ đồ AI vẽ → phải ghi nhãn *"Sơ đồ do AI tạo ra"*
- **Bộ dữ liệu 120 học sinh là DỮ LIỆU MÔ PHỎNG** (`seed_sample_data(seed=42)`, và bộ
  Excel trong `du_lieu_test/` với `seed=2026`), không phải khảo sát thật. Trình bày như
  số liệu thật là **bịa đặt dữ liệu**.
- Diễn giải, nhận xét kết quả kiểm thử → học sinh tự viết

**Nếu phiên mới có nhật ký AI cần cập nhật:** ghi thêm câu lệnh mới vào cuối Mục 3 của
artifact, cập nhật số liệu ở Mục 4.

---

## 7. Cách làm việc học sinh mong đợi

- **Trả lời bằng tiếng Việt.**
- **Kiểm chứng bằng thực nghiệm, đừng đoán.** Bài học đắt giá: hai lần đoán nguyên nhân lỗi
  `.exe` đều sai, chỉ khi đọc log build mới tìm ra sự thật. Học sinh đã phải tải về thử vô ích 2 lần.
- **Nói thẳng khi không chắc**, và nói rõ phần nào chưa kiểm chứng được.
- Chạy `pytest` trước khi commit. Giữ `i18n.js` ↔ `i18n_errors.py` đồng bộ.

---

## 8. Tài liệu tham chiếu

| Tài liệu | Nơi lưu |
|---|---|
| Giải thích thuật toán RB-DA (tiếng Việt, có sơ đồ) | artifact `ef3cc025-51d6-4bb8-a8ee-92ac23c945c8` |
| Kế hoạch kiểm thử mất dữ liệu | artifact `c0aa29df-b2b2-4e40-8e72-4adb63627a26` |
| Nhật ký AI (PDF in được) | artifact `1369e5c3-3d9f-4d8f-8c00-0328bc1b5131` |
| Tài liệu thuật toán + dữ liệu test | `TAI_LIEU_RBDA.zip` (đã gửi cho học sinh) |
| README chi tiết | `rbda-kiosk/README.md` |

**Lưu ý:** 4 file được nhắc trong chú thích code nhưng **chưa bao giờ được upload**:
`02_schema.sql`, `03_reference_rbda.py`, `06_ms_forms_transform.py`, `PACKAGING_HUONGDAN.md`.
