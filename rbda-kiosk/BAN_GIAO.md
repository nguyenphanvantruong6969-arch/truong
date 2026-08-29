# BÀN GIAO NGỮ CẢNH — Dự án RB-DA

> **Đọc file này đầu tiên khi bắt đầu phiên làm việc mới.**
> Cập nhật lần cuối: 29/08/2026 · 152 test pass

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
| Test | **152 test, tất cả pass** (`./.venv/bin/python -m pytest -q`) |
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

### AI viết mới (đã trích dẫn đầy đủ trong nhật ký AI)
- `i18n.js` (830) + `i18n_errors.py` (415) — từ điển song ngữ vi/en, **phải luôn khớp nhau**
  (test `test_i18n_sync.py` bắt buộc)
- `recovery.py` / `recovery.html` / `recovery.js` — màn hình phục hồi khi `app.db` hỏng
- `browser_host.py` (237) — chế độ chạy dự phòng bằng trình duyệt
- `tests/` — 10 file, 152 test (có 1 file chạy giao diện thật bằng Playwright)
- `mau_csv/` — 5 file CSV mẫu + `HUONG_DAN_CSV.md` (định dạng nhập liệu)

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

10. **CSV học sinh KHÔNG gán được `reserve_group`.** Đây là khoảng trống đã biết,
   không phải bug: học sinh tạo bằng CSV có nhóm dự trữ rỗng, phải vào màn
   hình 04 gán riêng (có `bulk_set_reserve_group`). Quên bước này thì cơ chế
   dự trữ của RB-DA vô hiệu mà pipeline **không báo lỗi**. Đã ghi cảnh báo
   ở `mau_csv/HUONG_DAN_CSV.md` và README. Nếu sau này muốn bịt hẳn, hướng
   đúng là thêm cột `reserve_group` tuỳ chọn vào CSV nguyện vọng.

11. **Ngưỡng tự tắt là 120 giây, KHÔNG được hạ xuống.** Trình duyệt bóp thắt
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
- **`reserve_group` của HỌC SINH chưa nhập được bằng CSV** (xem mục 4.10).
  Của CLB thì đã có trong file danh sách CLB.
- **Chưa có nút "Sao lưu ngay" / "Khôi phục"** trong app thường; hiện chỉ
  tự sao lưu trước mỗi lần chạy pipeline, còn khôi phục thì chỉ xuất hiện
  ở màn hình recovery — tức là SAU KHI DB đã hỏng. Quy trình sao lưu đã
  chốt là copy tay file `.db` qua USB (mục 4.1), nên một nút "Xuất bản sao
  lưu ra USB" sẽ khớp đúng quy trình đó.

**Chưa test được trong sandbox:** cửa sổ pywebview thật, thao tác chuột/cảm ứng trên máy kiosk thật.

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
- **Bộ dữ liệu 120 học sinh là DỮ LIỆU MÔ PHỎNG** (`seed_sample_data(seed=42)`), không phải
  khảo sát thật. Trình bày như số liệu thật là **bịa đặt dữ liệu**.
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
