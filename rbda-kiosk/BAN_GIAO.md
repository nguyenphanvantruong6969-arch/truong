# BÀN GIAO NGỮ CẢNH — Dự án RB-DA

> **Đọc file này đầu tiên khi bắt đầu phiên làm việc mới.**
> Cập nhật lần cuối: 01/09/2026 · 381 test pass

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
| Test | **381 test, tất cả pass** (`xvfb-run -a ./.venv/bin/python -m pytest -q`) |
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
- `tests/` — 28 file test, 381 test case (5 file chạy giao diện thật bằng Playwright + Chromium)
- `mau_csv/` — 5 file CSV mẫu + 3 file Excel mẫu + `HUONG_DAN_CSV.md`
  + `tao_mau_excel.py` (sinh lại bộ Excel từ bộ CSV)
- `du_lieu_test/` — **ba bộ dữ liệu MÔ PHỎNG**, mỗi bộ một mục đích khác nhau:
  - `TEST_01..04` (120 em, 10 CLB) + 1 tệp **cố ý sai 6 chỗ** — kiểm tra phần mềm
    có cảnh báo không. Sinh bằng `tao_du_lieu_test.py`, seed 2026
  - `bo_sach/` (140 em, 12 CLB) — chạy thử quy mô gần thật, **0 cảnh báo**,
    xếp 140/140. Seed 9090
  - `vi_du_huong_dan/` (10 em, 4 CLB) — bộ dạy học đi kèm `HUONG_DAN_SU_DUNG.md`,
    số liệu **viết tay** để in trọn vào hướng dẫn. Xem README của nó
  - `NHAP_TAY.md` — kịch bản gõ tay 8 em / 3 CLB cho các màn hình mà đường nạp
    tệp không chạm tới
- `HUONG_DAN_SU_DUNG.md` — hướng dẫn vận hành 13 mục, viết cho người **chưa từng
  mở phần mềm**. Có bản trang web để gửi cho giám khảo (xem nhật ký AI).
  Mọi con số trong đó lấy từ số đo thật của `vi_du_huong_dan/`, và
  `tests/test_vi_du_huong_dan.py` khoá lại — bộ mẫu lệch là hướng dẫn nói dối

---

### LỖI 13 — app chết sau một lúc mở (30/08) — ĐÃ SỬA

**Triệu chứng học sinh gặp:** mở app một lúc rồi quay lại, kéo file vào thì mọi
file đều báo `TypeError: Failed to fetch`. Giao diện vẫn hiện đầy đủ, số liệu vẫn
đó, nhưng không thao tác nào chạy.

**Nguyên nhân:** `browser_host.py` đếm ping do `setInterval` gửi, không có ping quá
120 giây thì tự tắt máy chủ. Giả định đằng sau con số 120 là "trình duyệt bóp ping
thưa xuống ~1 lần/phút" — **giả định đó SAI**. Chromium hiện **đóng băng hẳn** bộ
đếm giờ của trang bị che (intensive throttling), và Edge trên Windows bật thêm
**Efficiency mode** — nhìn thấy rõ ngay trong ảnh Task Manager học sinh gửi
trước đó: dòng *Tab: Phân bổ Câu lạc bộ* mang nhãn *Efficiency mode*.

Ping không thưa đi, nó **ngừng hẳn**. Máy chủ tự tắt trong khi cửa sổ vẫn mở.
Trình duyệt giữ lại hình đã vẽ nên nhìn như app còn sống.

**Cách sửa:** tín hiệu chính không còn là bộ đếm giờ mà là **một socket đang mở**.
Trang mở `EventSource("/__alive__")` và giữ nguyên. Trình duyệt **không** đóng băng
socket — nó chỉ đóng băng bộ đếm giờ. Cửa sổ còn mở thì kết nối còn đó; đóng cửa sổ
thì đứt ngay và máy chủ biết tức khắc. Ping cũ giữ lại làm lưới đỡ cho trường hợp
kết nối đó không thiết lập được lần nào (lúc đó vẫn dùng ngưỡng 120 giây cũ).

**Đã kiểm bằng Chromium THẬT** (Playwright + Xvfb): dừng hẳn mọi `setInterval` của
trang để giả lập đóng băng, hạ ngưỡng ping xuống 3 giây, chờ 9 giây — gọi backend
vẫn **thành công**. Với cách cũ thì đã chết từ giây thứ 3.

**Sửa kèm:** nhánh `open_browser=False` không gọi `server_close()`, nên sau khi
dừng, cổng vẫn mở: kết nối mới bắt tay được nhưng không ai trả lời, bên gọi **treo
vô hạn** thay vì nhận lỗi rõ ràng. Chính chỗ này làm bộ test treo lúc phát hiện.

### Soát lại vòng NẠP → XUẤT (30/08) — tìm thêm 2 lỗi im lặng

Chạy 7 ca hiểm của vòng nạp-xuất. 5 ca đạt ngay. Hai ca hỏng, cả hai đều im lặng:

**Lỗi 11 — `csv.Sniffer` làm vỡ ô có dấu nháy kép.** `sniff()` trả về
`doublequote=False`, tức bỏ quy ước `""` của CSV. Ô `"Trần ""Bo"" Văn A, Jr."` bị
cắt ngay dấu phẩy; phần đuôi `Jr."` trôi sang cột kế bên và bị hiểu là mã club. Cả
dòng bị bỏ, kèm cảnh báo *"club không tồn tại"* **chẳng liên quan gì tới nguyên
nhân thật** — người nhập sẽ đi tìm sai chỗ. Tên CLB tiếng Việt rất hay có dấu
nháy (`CLB "Vì Cộng Đồng"`). Đã sửa: chỉ lấy **dấu phân cách** từ Sniffer, phần
quy ước trích dẫn dùng `csv.excel` chuẩn. Có test canh `;` và Tab vẫn nhận đúng.

**Lỗi 12 — tệp của lần xuất trước còn sót lại.** Xuất lần hai mà một CLB không còn
ai vào thì tệp `.csv` của nó từ lần một **vẫn nằm nguyên**, trông y hệt tệp thật.
Giáo viên cầm nhầm đi tổ chức một CLB không còn học sinh nào. Đã sửa: dọn `.csv`
cũ trong đúng thư mục `_theo_club` trước khi ghi. Có test canh **không** đụng vào
tệp khác của người dùng để trong đó.

**Sửa thêm (không phải lỗi, là lỗ hổng):** ô bắt đầu bằng `= + - @` bị Excel TÍNH
như công thức — học sinh tên `=1+1` hiện ra là `2`. Nay thêm dấu nháy đơn ở đầu.

Ca thứ 7 tôi tưởng hỏng hoá ra **test viết sai**: `delete_club` từ chối xoá club
còn nguyện vọng/kết quả tham chiếu tới (`cannot_delete_club_referenced`) — phần
mềm đang bảo vệ dữ liệu đúng như phải thế.

Đã đối chứng A/B với bản trước khi sửa: bản cũ nạp tên có dấu nháy ra **0 học
sinh**, bản mới ra **1**; bản cũ để sót `clb_b.csv`, bản mới sạch.

### Biểu tượng ứng dụng (30/08)

Học sinh tự thiết kế, nộp dạng SVG. Nguồn gốc duy nhất là `logo.svg`;
`tao_logo.py` vẽ lại bằng Pillow ở độ phân giải gấp 8 rồi thu nhỏ, sinh ra
`logo.png` (512, nền trong suốt) và `logo.ico` (7 cỡ, 16→256). **Sửa hình thì sửa
`logo.svg` rồi chạy lại `tao_logo.py`, đừng sửa tay tệp .png/.ico.**

Gắn ở hai chỗ vì có hai đường hiển thị: `icon="logo.ico"` trong `kiosk.spec` cho
tệp `.exe`, và `<link rel="icon">` trong `index.html`/`recovery.html` cho cửa sổ
trình duyệt dự phòng. Ảnh chụp ngày 30/08 là lúc đường dự phòng đang chạy, nên quả
địa cầu học sinh nhìn thấy khi đó là biểu tượng mặc định của trang web, không phải
của `.exe`. Từ 31/08 đường chính chạy được, biểu tượng lấy từ `logo.ico`.

`tests/test_bieu_tuong.py` (8 test) canh cả hai, kèm một test soát mọi tệp khai
báo trong `datas` của `kiosk.spec` đều tồn tại thật.

### Vì sao ba phiên phải ĐOÁN lỗi pythonnet (30/08) — đã sửa gốc

`main.py` bắt được ngoại lệ khi pywebview hỏng rồi ghi vết lỗi ra
**`sys.stderr`** — mà bản đóng gói chạy `console=False` thì **không có stderr nào**.
Vết lỗi bị vứt đi đúng lúc nó xảy ra. Đó mới là lỗi gốc: không phải pywebview hỏng,
mà là hỏng **mà không ai biết vì sao**.

Nay có `chan_doan.py`:
- Ghi mọi thứ vào **`loi_khoi_dong.txt`** cạnh `app.db` — nối thêm, không ghi đè.
- Ghi cả khi THÀNH CÔNG, để biết lần nào chạy đường nào.
- Không bao giờ ném lỗi ra ngoài (hỏng phần ghi log mà làm chết app thì tệ hơn).

**Giả thuyết đang thử — chưa kiểm chứng được:** Windows gắn dấu "tải từ Internet"
(luồng NTFS `Zone.Identifier`) vào mọi tệp giải nén từ `.zip` tải về, và .NET
Framework **từ chối nạp assembly mang dấu đó**. Khớp đúng triệu chứng: thông báo
lỗi nêu rõ đường dẫn tới `Python.Runtime.dll`, tức tệp CÓ ở đó, .NET tìm thấy
nhưng không nạp.

Hai lớp cùng chữa nguyên nhân đó:
1. `chan_doan.go_dau_tai_ve()` xoá luồng `Zone.Identifier` khỏi mọi `.dll/.exe/.pyd`
   trong gói, chạy **trước** `import webview`. Không cần quyền Administrator.
2. `PhanBoCauLacBo.exe.config` với `loadFromRemoteSources enabled="true"` — bảo .NET
   bỏ qua dấu ngay từ đầu. **Phải nằm cạnh `.exe`**, không phải trong `_internal/`;
   quy trình build chép nó vào đúng chỗ, có test canh.

**Máy phát triển là Linux — không có .NET Framework lẫn luồng NTFS, nên hai lớp này
CHƯA CHẠY THẬT lần nào.** Đó chính là lý do phải có lớp ghi log: nếu giả thuyết sai
thì lần này biết sai ở đâu thay vì đoán lần thứ tư.

**Người dùng nay nhìn thấy đang chạy đường nào:** góc dưới thanh bên hiện
"Cửa sổ ứng dụng riêng" hoặc "Chế độ dự phòng (trình duyệt)" (màu vàng). Trước đây
phải mở Task Manager mới biết — và khi không ai biết thì không ai sửa.

### Cột điểm trong file nhập (30/08) — PHÁ LỆ ĐÓNG BĂNG CÓ CHỦ Ý

Học sinh yêu cầu "dữ liệu chạy ra kết quả có nghĩa". Đào ra thì gặp một chỗ chặn
thật: **không có điểm thì mọi em rơi xuống Tầng 2 và chỉ xếp bằng bốc thăm** —
vòng thi coi như không tồn tại. Mà phần mềm khi đó **không có đường nạp điểm từ
file**: 396 ô điểm phải gõ tay, khoảng 18 phút.

Đã thêm cột điểm vào **file chọn CLB muốn thi** (chỉ file đó):
- Dạng rộng: `score_N` ghép với `test_club_N` theo **hậu tố số**, không theo vị
  trí cột. Ghép theo vị trí thì bỏ trống `test_club_2` sẽ gán điểm nhầm club.
- Dạng dài: thêm cột `score`.
- Không bắt buộc. Thiếu cột thì hành vi y hệt trước.
- Ô điểm hỏng chỉ mất **riêng ô đó**, giữ nguyên lựa chọn thi.
- Điểm ghi bằng `club_id` ĐÃ KHỚP qua `_khop_club_id`, không phải chuỗi thô.
- File nguyện vọng có lẫn `score_*` → cảnh báo `csv_scores_ignored_here`.

Đây là **thêm tính năng trong thời gian đóng băng**, học sinh quyết định. Rủi ro
thấp: gói gọn trong một nhánh của `import_test_selection_csv`, 13 test riêng
(`tests/test_nap_diem_tu_file.py`), và ràng buộc "hai dạng cho kết quả giống hệt
nhau" vẫn được canh.

### Bố cục căn giữa (30/08)

`.main` có `max-width` nhưng thiếu `margin-inline: auto`, nên khối nội dung dính
sát mép trái cột `1fr` — màn hình 1900px thừa gần 700px bên phải. Nay căn giữa và
nới 980 → 1280px. Đo bằng Chromium thật ở ba bề rộng: 1900px cho lề 186px đều hai
bên, 1280px và 900px không tràn ngang.

### Bộ dữ liệu thiết kế lại cho cạnh tranh cao (30/08)

Bộ cũ cho 93/118 em được nguyện vọng 1 và chỉ **2 em** dùng tới suất dự trữ —
nhìn bảng kết quả như ai cũng được như ý, thuật toán không lộ ra là nó làm gì.

Ba thay đổi trong `tao_du_lieu_test.py` (giữ `SEED = 2026`):
1. Nguyện vọng bốc theo **độ hút**: 3 CLB "hot" trọng số 10, 3 CLB "nguội" 0.75.
2. Suất dự trữ chuyển sang **đúng các CLB chật**. Đặt ở CLB còn chỗ thì vô dụng.
3. Điểm nhóm dự trữ lệch thấp hơn (6.3/6.5 so với 7.6) — đây là cách dựng số liệu
   để suất dự trữ phải làm việc, **không** phải nhận định về học sinh diện chính sách.

Kết quả đo được: **108/120 được xếp**, nguyện vọng 1 **59%** (cũ 79%), **10 em**
vào bằng suất dự trữ (cũ 2), 12 em chưa được xếp, 4 CLB đầy và 6 CLB thừa chỗ,
**0 cảnh báo dữ liệu** sau khi nạp (vì điểm đã có sẵn trong file).

**Bộ này CỐ Ý thiết kế cho cạnh tranh cao, không mô phỏng phân bố tự nhiên.** Mọi
tài liệu phải ghi rõ điều đó — trình bày như phân bố nguyện vọng có thật là bịa
đặt dữ liệu.

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

### ✅ ĐÃ ĐÓNG (01/09) — lỗi 24: cổng khởi động hỏi sai câu hỏi

Triệu chứng học sinh báo: *"mới cài, mở lần đầu thì thường bị lỗi backend không
kết nối được"*. Câu đó khớp đúng một chuỗi có thật trong mã (`app.js`,
`callApi`): `` `Backend not ready yet (${name})` `` — và chuỗi này **không đi qua
`I18N`**, nên nó hiện thẳng bằng tiếng Anh vào giao diện tiếng Việt.

**Nguyên nhân đọc được từ mã nguồn pywebview 6.2.1 trong `.venv`, không phải suy
đoán.** pywebview **không** dựng `window.pywebview` trong một nhịp:

| Tệp | Việc |
|---|---|
| `webview/js/api.js` | `window.pywebview = { …, api: {} }` — **api RỖNG** |
| `webview/js/finish.js` | `_createApi(…)` rồi mới `dispatch pywebviewready` |

`webview/util.py`, `generate_js_object()` chạy hai nhịp đó bằng **hai lệnh
`run_js` tách rời, trên một luồng riêng, có phản chiếu Python xen giữa**. Trong
khe hở đó `window.pywebview` **đã có thật** mà gọi hàm nào cũng trượt. Trên
Windows việc này còn chạy **sau khi trang đã tải xong**
(`webview/platforms/edgechromium.py`, trong `on_navigation_completed`).

Cổng cũ chỉ hỏi `if (window.pywebview)` rồi hẹn giờ **một phát 300 ms**. Gọi T1 =
lúc nhịp 1 xong, T3 = lúc sự kiện bắn:

| | Điều kiện | Chuyện xảy ra |
|---|---|---|
| A | 300 ms < T1 | đúng — nhưng chỉ xảy ra khi máy **chậm** |
| **B** | T1 < 300 ms < T3 | `init()` chạy với **api rỗng** → `"Backend not ready yet"` |
| **C** | T3 < 300 ms | `init()` chạy **hai lần** — cờ `appInit` chỉ được đặt ở nhánh hẹn giờ, nên đường sự kiện không đánh dấu gì |

**Đo được cả bốn hậu quả** (`tests/test_khoi_dong_backend.py`, bản chưa vá):

| Đo | Kết quả |
|---|---|
| Ca B | `Không đọc được trạng thái tổng quan: Backend not ready yet (get_dashboard_status)` |
| Ca C | `init()` chạy **2 lần** |
| Nút đổi ngôn ngữ | bấm **một** cái, ngôn ngữ **không đổi** |
| Nút xoá hai bước | `reset_data` chạy **2 lần** |

Hai dòng cuối là vì cả **40** chỗ gắn sự kiện trong `app.js` đều dùng
`addEventListener`, **không chỗ nào** dùng `.onclick` (đã đếm) — khởi động hai
lần là **gắn đôi toàn bộ nút**. Nút đổi ngôn ngữ gọi `setLang` hai lượt
(vi→en→vi) nên **trông như chết**; `armTwoStepConfirm` sinh hai bao đóng, mỗi cái
một biến `armed` riêng, nên bấm lần hai là `onConfirmed()` chạy hai lượt.

> **Lỗi này giải thích luôn báo cáo "đổi ngôn ngữ bị giật" của phiên trước.** Lần
> đó đã sửa một nguyên nhân có thật (cất câu đã dịch), nhưng đây là nguyên nhân
> **thứ hai, độc lập** — và nó mới giải thích được phần "lúc được lúc không".

**Sửa:** tách `apiSanSang(name)` để cổng khởi động hỏi **chính** điều kiện mà
`callApi` đòi hỏi (hàm gọi được, không phải đối tượng tồn tại); thay hẹn giờ
một-phát bằng **hỏi vòng 50 ms, hạn 20 giây**; đặt cờ **ngay trong**
`khoiDongMotLan()` nên mọi đường vào đều qua nó; quá hạn thì báo bằng tiếng Việt
và **chỉ tên tệp `loi_khoi_dong.txt`** để lần sau không phải đoán. `recovery.js`
là **bản sao nguyên văn** của cùng cổng đó nên vá y hệt — riêng ở đó, gắn đôi làm
`start_fresh` (nút xoá sạch để bắt đầu lại) chạy hai lượt, **đã đo, đã đóng**.

Cố tình **không** nghe `pywebviewready` song song với hỏi vòng: điều kiện hỏi
vòng mạnh hơn sự kiện, và hai đường vào cho cùng một việc chính là cách lỗi này
sinh ra lần đầu.

**Vì sao 381 test không bắt được — quan trọng, đừng để người sau vấp lại:** mọi
test giao diện đều đi qua `browser_host.serve(...)`, mà `browser_host` chèn cầu
nối giả lập **trước `</head>`**, đồng bộ, `api` là Proxy luôn sẵn sàng. Nghĩa là
**không test nào từng chạy qua con đường người dùng Windows thật đi**. Có test
giao diện **không** đồng nghĩa với đã phủ đường khởi động. File test mới phục vụ
trang bằng `http.server` tĩnh rồi **mô phỏng đúng hai nhịp của pywebview** bằng
`add_init_script`, có kiểm soát thời điểm.

**Tác động lên kết quả đã công bố: không có.** Lỗi thuần tầng khởi động giao diện,
không đụng thuật toán.


### ✅ ĐÃ ĐÓNG (01/09) — lỗi 23: ô điểm nuốt mất dấu phẩy, `8,5` thành `85`

Tìm ra khi dò lại sau khi đã sửa lỗi 21–22. **Nặng hơn cả hai lỗi đó.**

Đo trong Chromium thật, cả locale `en-US` lẫn `vi-VN`:

```
Gõ "8,5" vào ô điểm  ->  .value === "85"
                         validity.valid === true
```

Ô điểm là `<input type="number">`. Trình duyệt **nuốt dấu phẩy** rồi **báo là hợp
lệ** — không gạch đỏ, không thông báo. Điểm bị nhân lên **10 lần**, im lặng.

Khác mọi lỗi điểm khác ở một chỗ quyết định: **không cần ai gõ nhầm.** `8,5` là
cách viết thập phân bình thường của tiếng Việt. Gõ đúng thói quen, máy hiểu sai.

**Nghịch lý ngay trong dự án:** nạp tệp Excel thì `8,5` lưu đúng thành 8.5, vì
`_doc_diem()` xử lý dấu phẩy và chú thích ghi rõ *"Excel bản tiếng Việt lưu 8,5"*.
Nhưng `submit_club_scores` gọi `float()` thẳng, không dùng hàm đó. Lại là
**"hai cửa, hai luật"** — cùng loại với lỗi 21.

**Sửa hai nửa:**

1. `app.js` — `type="number"` → `type="text"` + `inputMode="decimal"`. Trình duyệt
   hết cơ hội đụng vào dấu phẩy; máy cảm ứng vẫn hiện bàn phím số. Mất mấy nút
   mũi tên tăng/giảm, với kiosk thì không tiếc. `.score-input` không có luật CSS
   nào phụ thuộc `type=number` (đã soát).
2. `api.py` — `submit_club_scores` dùng `_doc_diem()` thay `float()`. Sau đó hai
   cửa cùng một luật: `8,5` và `8.5` đều đúng, `abc` sai ở cả hai. `_doc_diem`
   còn chặt hơn `float()` ở chỗ loại `inf`/`nan`.

**Vì sao 363 test không bắt được:** tầng Python **mù hoàn toàn** — API chưa bao
giờ nhìn thấy dấu phẩy, vì trình duyệt đã xoá trước khi gửi. API nhận `"85"` và
lưu đúng `85`. Chỉ Chromium thật mới thấy. Đây là file test giao diện thứ **năm**
của dự án, và là lần thứ ba trong ngày một lỗi chỉ lộ ra ở trình duyệt.

`tests/test_giao_dien_cham_diem.py` kiểm **giá trị trong CSDL**, không kiểm
`.value` của ô — chính `.value` là chỗ lỗi ẩn nấp. Chạy với bản chưa vá: 3 test
đỏ, và một test cho thấy gõ `7,5` lưu ra **75,0**.

**Tác động lên kết quả đã công bố: không có.** Mọi bộ dữ liệu nạp qua tệp, không
qua màn hình chấm điểm.


### ✅ ĐÃ ĐÓNG (01/09) — lỗi 21 và 22: điểm không có chốt chặn nào

Lỗi duy nhất còn lại có thể làm **sai người trúng tuyển**. Đo trên bộ ví dụ 10 em,
gõ `70` thay vì `7.0` cho HS10:

| Em | Trước | Sau |
|---|---|---|
| HS10 | *(chưa xếp)* | **CLB Bóng rổ** |
| HS02 | CLB Bóng rổ | **CLB Mỹ thuật** |
| HS08 | CLB Mỹ thuật | **CLB Nấu ăn** |

**Một lỗi gõ, ba em đổi chỗ** — em bị đẩy ra lại đi đẩy em khác. Và 0 cảnh báo.

**Lỗi 21 — hai cửa, hai luật.** Cùng giá trị `-9`: đường nạp tệp từ chối
(`csv_score_negative`), màn hình Chấm điểm **nhận**. Bắt được hay không tuỳ giáo
viên đi cửa nào. Nay `submit_club_scores` từ chối điểm âm, mã lỗi `score_negative`,
và **điểm cũ không bị ghi đè** — có test canh riêng chỗ đó.

**Lỗi 22 — không có quy tắc nào soát điểm bất thường.** Nay có quy tắc rà soát
thứ 8: so mỗi điểm với **trung vị của chính CLB đó**.

> **KHÔNG đặt trần cứng ở 10.** Trường có thể chấm thang 100, chặn cứng là chặn
> nhầm. So với trung vị thì thang nào cũng đúng, và bắt được cả hai phía.

**Ngưỡng 3,0 chọn bằng số đo, không phải cảm tính:**

| | |
|---|---|
| Tỉ lệ (điểm cao nhất / trung vị) trong một CLB — cao nhất trên **579 ô điểm thật** | **1,42** |
| Tỉ lệ khi gõ lệch dấu chấm | **≈ 10** |
| Quét thử hệ số 1,5 | **11 cảnh báo giả** |
| Quét thử hệ số 2,0 · 2,5 · 3,0 | **0 cảnh báo giả** |

Lấy 3,0 để cách ca thật tệ nhất 2,1 lần mà vẫn thừa sức bắt lỗi gõ. Bắt được
`70`, `85` và `0.85`; không báo với `6.0` (điểm thấp thật) và không báo với
trường chấm thang 100. CLB dưới 3 điểm thì bỏ qua — chưa có phân bố nào để so.

**Tác động lên kết quả đã công bố: không có.** Lỗi 21 chỉ từ chối thứ chắc chắn
sai (không bộ dữ liệu nào có điểm âm); lỗi 22 chỉ **thêm cảnh báo**, không chặn
ai chạy. Cả hai bộ dữ liệu vẫn **0 cảnh báo**, kết quả không đổi một dòng.

**Còn lại không sửa được:** một điểm sai *vừa phải* — 9 thay vì 8 — thì không
cách nào phát hiện. Đã ghi vào mục *Giới hạn đã biết* của hướng dẫn.


### ✅ ĐÃ ĐÓNG (01/09) — lỗi 19: bốc thăm phụ thuộc THỨ TỰ NHẬP học sinh

Học sinh hỏi *"chạy trên máy khác có ra cùng kết quả không?"* — hỏi đúng chỗ hiểm.

`load_from_sqlite` đọc `SELECT student_id, stb_number, reserve_group FROM students`
**không có `ORDER BY`**. Truy vấn cần cột ngoài chỉ mục nên SQLite quét bảng, trả
về theo **thứ tự chèn**. `generate_stb_lottery` rồi `shuffle` đúng danh sách đó,
mà `shuffle` phụ thuộc thứ tự đầu vào.

| Thử nghiệm (10 em điểm bằng nhau, `seed=42`) | Kết quả |
|---|---|
| Chèn HS01→HS10 vs HS10→HS01, **trước bản vá** | **6/10 em khác CLB** |
| Cùng thử nghiệm, **sau bản vá** | **0 em khác** |

Chữa bằng **một dòng**: `sorted(student_ids)` trước khi xáo, đặt **trong hàm**
`generate_stb_lottery` chứ không ở chỗ gọi — chính hàm đó hứa *"seed cố định để
tái lập kết quả khi kiểm tra/audit"*, nên nó phải tự giữ lời hứa, và hàm có hai
chỗ gọi.

**Không đổi bản chất thuật toán.** RB-DA không sửa dòng nào. Xáo trên danh sách
đã sắp vẫn cho hoán vị ngẫu nhiên đều — đo được: `HS01` nhận số 9/12, số 0 rơi
vào `HS08`. Đã đo trên hai bộ dữ liệu đã công bố: **0 em đổi CLB**, bảng trong
hướng dẫn khớp từng dòng.

> **Câu chữ cho báo cáo — chỗ này rất dễ nói sai:**
> **KHÔNG viết** "số bốc thăm dựa trên mã học sinh" — nghe như em tên A có lợi
> hơn em tên Z, và không đúng.
> **Viết đúng:** *bốc thăm không phụ thuộc thứ tự nhập liệu*. Mã học sinh chỉ
> dùng để danh sách đầu vào luôn ở một trật tự cố định; xáo xong thì mã không
> còn vai trò gì.

### ✅ ĐÃ ĐÓNG (01/09) — lỗi 20: biểu đồ lấp đầy chưa bao giờ vẽ được thanh chính

Học sinh gửi ảnh: CLB đầy **14/14** mà máng trắng trơn, còn đúng 4 CLB có suất
dự trữ thì hiện một đoạn vàng ngắn.

`.fill-bar` là `<span>` mà CSS chỉ đặt `height` và `background`, **không đặt
`display`**. `width`/`height` **không áp dụng cho phần tử inline** → thanh không
có kích thước. Đoạn dự trữ vẽ được **chỉ vì** JS gắn `position:absolute` nội
tuyến, mà absolute thì bị ép thành block.

Đo trong Chromium thật, trước bản vá:

| CLB | Số | Thanh chính |
|---|---|---|
| Âm nhạc | 14/14 | `display:inline`, css `100%` → **vẽ ra 0 px** |
| Khoa học | 5/10 | `display:inline`, css `50%` → **vẽ ra 0 px** |

Ba việc đi cùng nhau:

1. **Máng thành `display:flex`** — con của flex tự động thành block, nên không
   đoạn nào có thể rơi lại vào inline. Chọn flex thay vì thêm `display:block` là
   có chủ ý: triệt **cả lớp lỗi**, không chỉ ca đang gặp.
2. **`get_club_fill_stats` trả thêm `matched_reserve`** — số em **thực sự** vào
   bằng suất dự trữ. Bản cũ vẽ theo `reserve_capacity`, tức chỉ tiêu của CLB,
   một thuộc tính của CLB chứ không phải điều đã xảy ra.
3. **Vẽ hai đoạn liền nhau**, không chồng mờ: vàng = vào bằng dự trữ, xanh = vào
   ở chỉ tiêu chung, cộng lại đúng bằng tỉ lệ lấp đầy in bên phải.

Chú giải cũng sai theo nên sửa: *"Có suất dự trữ"* → *"Vào bằng suất dự trữ"*.

Đo lại trên bộ 140 em: mọi thanh khớp con số của nó, và bốn đoạn vàng cộng lại
đúng **16 em** — bằng số em vào bằng dự trữ đã ghi trong tài liệu.

**Vì sao sống sót lâu vậy:** `test_api.py` và `test_kich_ban_nhap_tay.py` có gọi
`get_club_fill_stats`, và **API luôn trả về đúng số**. Sai nằm ở tầng CSS, nơi
tầng Python mù hoàn toàn — y hệt lỗi i18n cùng ngày. Nay có
`tests/test_giao_dien_bieu_do.py` đo **bề rộng vẽ ra thật**
(`getBoundingClientRect`), không đo thuộc tính CSS: chính `width:100%` mà vẽ ra
0 px là cái bẫy đã giấu lỗi này từ đầu.


### ✅ ĐÃ ĐÓNG (01/09) — lỗi đổi ngôn ngữ ở ô nạp tệp

Học sinh báo "chuyển tiếng Việt/tiếng Anh bị lỗi". Dò bằng Chromium thật, quét cả
5 tab và đối chiếu 145 cặp chuỗi vi/en: **đổi tab bình thường không sót chuỗi
nào**. Lỗi chỉ hiện ở những trạng thái **đang dang dở**, và đúng ở khu vực người
dùng chạm vào đầu tiên.

| # | Tái hiện | Hiện tượng |
|---|---|---|
| 16 | Thả tệp → đổi ngôn ngữ | Hàng chờ vẫn ghi *"Nhận diện: Danh sách CLB"* |
| 17 | Nhập xong → đổi ngôn ngữ | Tóm tắt vẫn ghi *"Xong: 5 CLB mới…"* |
| 18 | Nút xoá đang chờ xác nhận → đổi ngôn ngữ | Nút vẫn ghi *"Bấm lần nữa để xoá…"* |

**Nguyên nhân chung, và đây là phần đáng viết vào báo cáo:** mã **dịch một lần
rồi cất câu đã dịch**. Vẽ lại bao nhiêu lần cũng ra nguyên tiếng cũ. Chữa bằng
cách cất **khoá + tham số**, gọi `t()` lúc vẽ — đúng khuôn mẫu `lastRenderedSteps`
đã dùng cho stepper từ trước, không nghĩ cách mới.

Lỗi 18 vốn **do thiết kế**: `applyStaticText()` cố ý bỏ qua phần tử
`.is-confirming` để nhãn không lệch khỏi trạng thái bên trong. Lý do đúng, cách
xử lý sai — nay **nhả hẳn nút** ra khi đổi ngôn ngữ.

`tests/test_giao_dien_doi_ngon_ngu.py` (4 test, Chromium thật). **Đã chạy thử với
bản chưa vá: 3 test đỏ.** Bản test đầu tiên của tôi xanh giả vì hạn chờ 8 giây
rộng hơn bộ đếm tự nhả 4 giây của chính nút — siết xuống 1,5 giây mới bắt được.
Test thứ tư là lưới an toàn cho tương lai, xanh cả hai bên là đúng.


### ✅ ĐÃ ĐÓNG (01/09) — hai lỗi lộ ra khi học sinh chạy thử bộ sạch

Học sinh nạp bộ `bo_sach/` (bộ được thiết kế để **không** sinh cảnh báo nào) rồi
vẫn thấy **1 cảnh báo nghiêm trọng**. Truy ra hai lỗi khác nhau.

**Tái hiện được, và đây là số đo:** nạp `TEST_01..04` (có file lỗi cố ý) rồi
chồng bộ sạch lên, không xoá gì → CSDL có **148** học sinh thay vì 140, còn đúng
**1 cảnh báo**, và chạy phân bổ ra **143/148** chứ không phải 140/140.

| # | Lỗi | Chữa thế nào |
|---|---|---|
| 14 | Cảnh báo "nhãn dự trữ không club nào dùng" nói có gõ sai chính tả nhưng **không nói em nào**. Hai cảnh báo ngay trên nó đều kèm mã học sinh; mục này bị bỏ sót | Thêm `sample` (tối đa 5 mã, đã sắp xếp) vào `get_data_health_report()` mục 4, và bổ sung câu chỉ đường tới chỗ chữa |
| 15 | **Không có đường nào trong app đưa dữ liệu về trống.** Nạp file cộng thêm học sinh, không bao giờ xoá — đúng như phải thế, nhưng khi đó cách duy nhất làm lại từ đầu là đóng app rồi đổi tên `app.db` ngoài File Explorer, việc không ai tìm ra | `reset_data(pham_vi, xac_nhan)` + khối **Vùng nguy hiểm** cuối tab Quản lý |

Lỗi 15 nguy hiểm ở chỗ **im lặng**: học sinh của lần chạy trước vẫn chiếm suất và
làm lệch kết quả mà không có dấu hiệu nào.

**Ba điều `reset_data()` bắt buộc làm, và lý do:**

1. **Kiểm tra xác nhận TRƯỚC, sao lưu SAU.** Đảo lại thì mỗi lần gọi nhầm vẫn đẻ
   ra một tệp `.bak` rác. Có test canh riêng cho thứ tự này.
2. **Tự sao lưu** bằng `_backup_db()` đã có sẵn (SQLite Backup API, không copy
   tệp thô). Test mở bản sao lưu ra đếm lại, chứ không chỉ kiểm tra tệp tồn tại.
3. **Mở khoá STB.** Bỏ qua thì lần chạy sau ghi nhật ký là "tái sử dụng STB" cho
   một bộ số bốc thăm không còn tồn tại — sai cho phần kiểm toán.

**Không xoá `run_history`** ở bất kỳ phạm vi nào: lược đồ ghi rõ bảng đó "không
bao giờ xoá/ghi đè". Xoá dữ liệu không được phép xoá dấu vết.

Sau bản vá, đúng tình huống trên: xoá → nạp lại → **0 cảnh báo, 140/140**.
`tests/test_bo_sach.py` khoá cả hai vế (khẳng định lỗi có thật, rồi khẳng định
bản vá chữa được), và `tests/test_giao_dien_xoa_du_lieu.py` mở Chromium thật để
bắt lỗi đặt nhầm bảng i18n — loại lỗi chỉ lộ ra ở trình duyệt.

### ✅ ĐÃ ĐÓNG (31/08) — lỗi `.exe` Windows, lỗi cũ nhất của dự án

Mở từ 27/08, đóng ngày 31/08. **Nguyên nhân gốc không nằm trong mã nguồn.**

```
RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize
from ...\_internal\pythonnet\runtime\Python.Runtime.dll
```

**Nguyên nhân thật:** Windows gắn dấu "tải từ Internet" (luồng NTFS
`Zone.Identifier`) vào **mọi tệp** giải nén từ `.zip` tải về, và .NET Framework
**từ chối nạp assembly mang dấu đó**. Vì thế thông báo lỗi nêu rõ đường dẫn — tệp
CÓ ở đó, .NET tìm thấy, chỉ là không chịu nạp.

**Bằng chứng từ máy học sinh** (`loi_khoi_dong.txt`):

```
[2026-08-31 15:34:42] go dau tai-ve trong ...\_internal:
                      {'da_go': 173, 'bo_qua': 0, 'loi': 0}
[2026-08-31 15:34:42] cua so goc (pywebview) mo THANH CONG
```

Đọc kỹ ba con số đó:
- `da_go: 173` — 173 tệp mang dấu, mã tự gỡ hết
- **`bo_qua: 0`** — không một tệp nào sạch sẵn, tức học sinh **KHÔNG** unblock tay;
  chính mã làm. Nghĩa là nó tự chạy trên **máy bất kỳ**, kể cả máy giám khảo.
- Cùng một giây, pywebview mở thành công

Task Manager xác nhận: `PhanBoCauLacBo.exe` là tiến trình riêng; nhóm
`msedgewebview2.exe` (WebView2 Runtime) vẽ nội dung **bên trong** cửa sổ của nó.

**Cách chữa — hai lớp, xem `chan_doan.py`:**
1. `go_dau_tai_ve()` xoá luồng `Zone.Identifier` khỏi mọi `.dll/.exe/.pyd` trong
   gói, chạy **TRƯỚC** `import webview`. Không cần quyền Administrator.
   **Đảo thứ tự là mất tác dụng hoàn toàn** — có test canh (`test_chan_doan.py`).
2. `PhanBoCauLacBo.exe.config` với `loadFromRemoteSources enabled="true"` — bảo
   .NET bỏ qua dấu ngay từ đầu. Phải nằm **cạnh** `.exe`, không phải trong
   `_internal/`.

### Vì sao ba phiên trước không tìm ra — phần đáng viết vào báo cáo

Lỗi thật không phải pywebview hỏng, mà là **hỏng mà không ai biết vì sao**:
`main.py` ghi vết lỗi ra `sys.stderr`, còn bản `console=False` **không có stderr**.
Bằng chứng bị vứt đi đúng lúc nó xảy ra. Ba phiên phải ĐOÁN, và đoán sai hai lần:

- **Lần 1 — đổ cho UPX.** Sai: máy build GitHub chưa bao giờ cài UPX.
- **Lần 2 — đổ cho thiếu tệp pythonnet.** Sai: hook chính thức đã chạy sẵn ở bản
  lỗi; log build run `33124799256` cho thấy build THÀNH CÔNG, `pythonnet 3.1.0`,
  `clr_loader 0.3.1`, `pywebview 6.2.1` đều có mặt.
- **Truy được chỗ ném lỗi:** `clr_loader/netfx.py` dòng 46–49, khi
  `pyclr_get_function` trả NULL. Đúng chỗ, nhưng vẫn không biết TẠI SAO.

Chỉ khi **ghi vết lỗi ra tệp** thay vì stderr thì mới kiểm chứng được giả thuyết
thay vì đoán tiếp. Bài học đáng viết: *thứ hỏng trước tiên không phải tính năng, mà
là khả năng biết được tính năng đã hỏng thế nào.*

### Câu chữ ĐÚNG cho báo cáo — dùng nguyên văn

> **Được viết:** phần mềm chạy trong cửa sổ ứng dụng của riêng nó; nội dung được vẽ
> bằng WebView2 Runtime — một thành phần có sẵn của Windows 10/11.
>
> **Được viết:** lỗi đóng gói đã tìm ra nguyên nhân gốc và đã chữa.
>
> **KHÔNG được viết:** *"không dùng gì của Microsoft"* — WebView2 là của Microsoft.
> Nói đúng là **dùng thành phần hệ điều hành**, không phải **chạy trong trình duyệt**.

### Còn lại chưa giải quyết

- **`ky_va_tin_cay.ps1` chưa chạy ở đâu bao giờ.** Nếu demo trên máy không có quyền
  Administrator thì nó vô dụng — cân nhắc bỏ hẳn cho gọn.
- **Trần cứng 10 nguyện vọng** (`api.py:1281`). Thử tải cho thấy với 50–100 CLB thì
  đây là giới hạn thật. Đã ghi số, không sửa vì đang đóng băng tính năng.

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

### ✅ TRỌN LUỒNG NẠP → CHẠY → XUẤT ĐÃ CHẠY TRÊN WINDOWS (01/09)

Bước cuối cùng của dự án chưa ai kiểm chứng — *"mở tệp xuất ra trên máy thật"* —
nay đã đóng. Học sinh chạy bộ `bo_sach/` trên máy Windows rồi gửi lại tệp kết
quả; đối chiếu với lần chạy trên Linux ở đây.

| Đối chiếu | Kết quả |
|---|---|
| Số dòng | 140 — khớp |
| **Số dòng KHÁC nhau giữa hai máy** | **0** |
| Phân bố nguyện vọng | 54 · 46 · 21 · 11 · 7 · 1 — khớp |
| Diện thường / dự trữ | 124 / 16 — khớp |
| Sức chứa 12 CLB | khớp từng CLB |
| Dấu BOM `utf-8-sig` | có |
| Xuống dòng | CRLF (chuẩn Windows) |
| Tiếng Việt | không dòng nào vỡ dấu; chuẩn hoá **NFC** |

**Điều đáng viết vào báo cáo:** cùng một bộ dữ liệu và cùng `seed = 42` thì
Windows và Linux cho ra **kết quả phân bổ giống hệt nhau tới từng dòng**. Thuật
toán tất định, không phụ thuộc hệ điều hành — nghĩa là kết quả **tái lập được**,
ai cầm dữ liệu cũng dựng lại được đúng bảng đó để kiểm chứng.

*Lưu ý khi đọc bảng kết quả:* dữ liệu mô phỏng có vài em **trùng họ tên**
(vd `HS009` và `HS021` cùng tên "Phan Đức Phúc"). Đây là ngẫu nhiên khi sinh tên,
không phải lỗi — hệ thống định danh bằng **mã học sinh**, không bằng tên.

Tệp kết quả **không đưa vào git**: đó là dữ liệu học sinh, dù ở đây là dữ liệu
mô phỏng thì vẫn giữ đúng quy tắc (mục 4).

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

**Diễn biến hai ngày, ghi lại đầy đủ vì đây là phần đáng viết vào báo cáo:**

- **30/08** — ảnh Task Manager cho thấy nhóm *Microsoft Edge (8)*, mọi tiến trình
  con là `msedge.exe`. Kết luận lúc đó: đang chạy bằng **chế độ dự phòng**, lỗi
  pythonnet vẫn còn.
- **31/08** — sau khi thêm phần ghi log và tự gỡ dấu tệp: nhóm đổi thành
  *WebView2 Manager*, tiến trình `msedgewebview2.exe`, và Task Manager có
  `PhanBoCauLacBo.exe` **là tiến trình riêng**. Log ghi `da_go: 173, bo_qua: 0` rồi
  *"cua so goc (pywebview) mo THANH CONG"*.

**Lỗi đã đóng.** Xem mục 5 để biết nguyên nhân gốc và bằng chứng đầy đủ.

Phân biệt hai tên tiến trình — chỗ này dễ nhầm và quan trọng cho báo cáo:

| Tiến trình | Là gì | Nghĩa là |
|---|---|---|
| `msedge.exe` | **Trình duyệt Edge** | App đang mượn trình duyệt để vẽ (đường dự phòng) |
| `msedgewebview2.exe` | **WebView2 Runtime** — thành phần hệ điều hành | App vẽ trong cửa sổ của chính nó (đường chính) |

Đường dự phòng **vẫn giữ nguyên trong mã**, làm lưới an toàn cho máy thiếu WebView2
Runtime. Địa vị của nó đổi từ *"đường đang chạy"* thành *"đường lẽ ra không bao giờ
chạy"* — góc dưới thanh bên nói rõ đang chạy đường nào.

**Điều kiện dùng thật, học sinh xác nhận 30/08:** dùng **chuột**, không phải màn
hình cảm ứng → mọi lo ngại về kích thước nút cho ngón tay là **không còn liên quan**.
Máy demo có thể là máy giám khảo, và có mạng ở phòng thi.

Hai hệ quả đã xử lý:
- Bản build nay được đưa lên mục **Releases** (tải bằng đường dẫn thường, không cần
  đăng nhập GitHub — tệp trong mục Actions thì BẮT BUỘC đăng nhập, trên máy người
  khác là rào cản thật).
- Bộ 120 học sinh cần **356 ô điểm** và phần mềm **không có đường nhập điểm từ tệp**
  — gõ tay hết mất ~18 phút, dài hơn thời gian demo. Đã dựng sẵn
  `du_lieu_test/app_DEMO_da_cham_diem.db` (nạp xong, chấm xong, 0 cảnh báo, cố ý
  chưa chạy phân bổ). Đây là **lỗ hổng tiện dụng còn lại đã biết**, không sửa vì
  đang đóng băng tính năng.

**Chưa kiểm chứng trên máy thật:** các bước SAU khi nạp dữ liệu (chấm điểm, chạy
phân bổ, xuất kết quả), và
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
