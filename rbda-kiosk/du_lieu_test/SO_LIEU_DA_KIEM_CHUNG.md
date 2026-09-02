# Số liệu đã kiểm chứng

> ### ⚠️ TOÀN BỘ SỐ Ở ĐÂY ĐO TRÊN **DỮ LIỆU MÔ PHỎNG**
> 120 học sinh do máy sinh (`tao_du_lieu_test.py`, seed 2026), **không phải khảo
> sát học sinh có thật**. Hơn nữa bộ này được **cố ý thiết kế cho cạnh tranh cao**
> để cơ chế thuật toán lộ ra — nó **không** mô phỏng một phân bố nguyện vọng tự
> nhiên. Trình bày các con số này như số liệu khảo sát thật là **bịa đặt dữ liệu**.

Đây là **số đo thô**, kèm cách đo lại. Phần nhận xét, giải thích ý nghĩa và kết
luận — **học sinh tự viết**, AI không tham gia.

Tái lập mọi số dưới đây:

```bash
./.venv/bin/python du_lieu_test/tao_du_lieu_test.py   # sinh lại 4 tệp Excel
./.venv/bin/python du_lieu_test/tao_db_demo.py        # dựng lại CSDL demo
./.venv/bin/python -m pytest -q                       # chạy bộ kiểm thử
```

---

## 1. Quy mô bài toán

| Đại lượng | Giá trị |
|---|---|
| Học sinh | 120 |
| Câu lạc bộ | 10 |
| Tổng chỉ tiêu | 130 chỗ |
| Trong đó là suất dự trữ | 12 chỗ (ở 4 CLB, đều là CLB đông người đăng ký) |
| Lượt đăng ký thi | 396 |
| Ô điểm nạp thẳng từ tệp Excel | 396 |
| Học sinh thuộc diện dự trữ | 26 em — `chinh_sach` 19, `khoi_10` 7 |
| Học sinh không thuộc diện nào | 94 em |

## 2. Kết quả phân bổ

Chạy với `seed = 42`. Điểm nằm sẵn trong cột `score_*` của `TEST_02`, **không
chấm tay ô nào**.

| Đại lượng | Giá trị |
|---|---|
| Được xếp | **108 / 120** |
| Chưa được xếp | 12 |
| Số vòng lặp thuật toán | 7 |
| Thời gian chạy | **0,011 giây** (cả 5 bước, gồm sao lưu và xuất tệp) |
| Tổng chỗ được dùng | 108 / 130 |
| Cảnh báo dữ liệu trước khi chạy | **0** |

### Được xếp theo nguyện vọng thứ mấy

| Nguyện vọng | Số em | Tỉ lệ trên số em được xếp |
|---|---|---|
| Thứ 1 | **64** | 59% |
| Thứ 2 | 28 | 26% |
| Thứ 3 | 10 | 9% |
| Thứ 4 | 6 | 6% |

### Diện trúng tuyển

| Diện | Số em |
|---|---|
| Thường (`general`) | 98 |
| Dự trữ (`reserve`) | **10** |

*10 trong 12 suất dự trữ được dùng tới. 26 em thuộc diện dự trữ, 10 em trong số đó
vào được **qua suất dự trữ**; số còn lại vào bằng điểm thường hoặc không được xếp.*

### Lấp đầy từng CLB

| Mã CLB | Đã xếp / Chỉ tiêu | Suất dự trữ | Tình trạng |
|---|---|---|---|
| `clb_bongda` | 20 / 20 | 4 | Đầy |
| `clb_tienganh` | 16 / 16 | 2 | Đầy |
| `clb_mythuat` | 12 / 12 | 3 | Đầy |
| `clb_tinhoc` | 12 / 12 | 3 | Đầy |
| `clb_amnhac` | 13 / 14 | 0 | thừa 1 |
| `clb_bongro` | 13 / 18 | 0 | thừa 5 |
| `clb_robotics` | 7 / 8 | 0 | thừa 1 |
| `clb_vanhoc` | 8 / 10 | 0 | thừa 2 |
| `clb_khoahoc` | 2 / 8 | 0 | thừa 6 |
| `clb_tinhnguyen` | 5 / 12 | 0 | thừa 7 |

Tệp xuất ra: **120 dòng** trong tệp tổng, **11 tệp** theo CLB (10 CLB + 1 tệp
`_chua_duoc_xep.csv`).

## 3. Tốc độ ở quy mô lớn hơn

Dữ liệu sinh ngẫu nhiên, đo trên cùng một máy:

| Quy mô | Nạp dữ liệu | Chạy phân bổ | Kết quả | Số vòng |
|---|---|---|---|---|
| 120 học sinh / 10 CLB | — | 0,011 s | 108/120 | 7 |
| 500 học sinh / 20 CLB | 0,03 s | 0,03 s | 500/500 | 21 |
| 2 000 học sinh / 40 CLB | 0,10 s | 0,14 s | 1 994/2 000 | 33 |

## 3b. Thử tải ở quy mô lớn

Bảng ở mục 3 chỉ là ba điểm đo. Bộ thử tải đầy đủ — **204 lần chạy**, quét số học
sinh, số CLB, số nguyện vọng, tổng chỉ tiêu và cách chia chỉ tiêu — nằm ở
`du_lieu_test/thu_tai/`, số liệu thô trong `ket_qua_thu_tai.csv`.

**Cố ý không chép số sang đây.** Chép là tạo ra hai bản dễ lệch nhau; đọc thẳng
tệp CSV hoặc trang báo cáo.

## 3c. Ảnh hưởng của seed bốc thăm

Chạy lại toàn bộ quy trình với **200 seed** (1–200) trên cùng một bộ dữ liệu, lấy
seed 42 làm mốc rồi đếm số em xếp khác mốc.

| Bộ dữ liệu | Số em | **Không bao giờ đổi** | Đổi CLB: ít nhất / TB / nhiều nhất | Số em được xếp | Cặp phá vỡ |
|---|---|---|---|---|---|
| `vi_du_huong_dan/` | 10 | **10 (100%)** | 0 / 0,0 / 0 | 9 – 9 | 0 |
| `bo_sach/` | 140 | **127 (90,7%)** | 0 / 6,0 / 11 | 139 – 140 | 0 |
| `TEST_0*.xlsx` | 120 | **116 (96,7%)** | 0 / 1,9 / 4 | 107 – 109 | 0 |

Khoá xếp hạng của mỗi CLB là `(-điểm, số_bốc_thăm)`
(`rbda_priority_pipeline.club_priority_order`) — **điểm đứng trước**, nên seed chỉ
chen vào được đúng hai chỗ: em **hoà điểm**, và em dự tuyển CLB mình **không thi**
(tầng 2). Số đo khớp: trên cả ba bộ, **không một em nào** đổi chỗ mà lại nằm
ngoài hai nhóm đó.

`vi_du_huong_dan/` là ca đối chứng sạch nhất: bộ này **không có em hoà điểm và
không có em tầng 2**, và kết quả là **0 em đổi chỗ trên cả 200 seed**.

### Seed có đổi được việc một em CÓ SUẤT hay không?

Có — và đây là câu hỏi quan trọng hơn hẳn chuyện đổi CLB. Đổi CLB là đổi chỗ
ngồi; mất suất là ra khỏi cuộc chơi. Đã tách ra đếm riêng:

| Bộ dữ liệu | Luôn có suất | Luôn không có suất | **Bấp bênh — seed quyết định** |
|---|---|---|---|
| `vi_du_huong_dan/` (10 em) | 9 (90,0%) | 1 (10,0%) | **0 (0,0%)** |
| `bo_sach/` (140 em) | 139 (99,3%) | 0 | **1 (0,7%)** |
| `TEST_0*` (120 em) | 107 (89,2%) | 11 (9,2%) | **2 (1,7%)** |
| **Gộp ba bộ (270 em)** | | | **3 (1,1%)** |

Ba em đó, và chỉ ba em đó, là toàn bộ chỗ mà may rủi quyết định chuyện có suất
hay không. Phân bố số em được xếp trên 200 seed:

| Bộ | Phân bố |
|---|---|
| `vi_du_huong_dan/` | 9 em: **200/200 seed** — không dao động chút nào |
| `bo_sach/` | 139 em: 46 seed · 140 em: 154 seed |
| `TEST_0*` | 107 em: 49 · 108 em: 101 · 109 em: 50 |

### Trong trường hợp nào thì một em rơi vào nhóm bấp bênh

Theo dấu từng em qua 200 seed:

| Em | Nguyện vọng | Kết cục |
|---|---|---|
| `HS122` (bộ sạch) | 6 nguyện vọng | `clb_vanhoc` **154/200** (77%) · không suất **46/200** (23%) |
| `HS037` (TEST) | **chỉ 2 nguyện vọng** | `clb_bongda` **107/200** (54%) · không suất **93/200** (46%) |
| `HS045` (TEST) | 4 nguyện vọng | không suất **106/200** (53%) · `clb_mythuat` **94/200** (47%) |

Điểm chung: em đó bị từ chối hết các nguyện vọng trên, **rơi xuống nguyện vọng
cuối cùng còn với tới được**, và ở đúng đó lại đứng ngay ranh giới chỉ tiêu
trong một nhóm hoà nhau. Thua lượt bốc thăm ở chỗ đó thì **không còn nguyện
vọng nào phía dưới** để rơi tiếp — nên mất suất luôn.

`HS122` rơi tới nguyện vọng thứ **5** (`clb_vanhoc`, một CLB em không thi, tức
tầng 2 xếp thuần theo bốc thăm). `HS037` chỉ có **2** nguyện vọng nên không có
lưới nào đỡ.

**Một điều đã thử và KHÔNG kết luận được:** ranh giới này **không** đoán trước
được bằng cách so điểm thô. Ví dụ `HS122` ở `clb_tinhoc` có 34 em điểm cao hơn
trong khi chỉ tiêu là 14 — nhìn tĩnh thì em đứng ngoài rất xa, nhưng phần lớn
34 em kia lại đỗ nguyện vọng trên của họ, nên ranh giới thật tụt xuống tới em.
Ranh giới ở đây **sinh ra từ chuỗi dây chuyền** của thuật toán, không phải từ
bảng điểm. Bộ dò ranh giới tĩnh đã viết thử **không bắt được ca nào**.

### "Nguyện vọng càng ngắn càng dễ bấp bênh" — đã kiểm, và chỉ đúng một nửa

Cả ba em bấp bênh đều ở bộ có nguyện vọng ngắn hơn, và `HS037` chỉ có 2 nguyện
vọng. Ba ca thì chưa kết luận được, nên làm thí nghiệm đối chứng: **cùng bộ sạch,
cùng điểm, cùng chỉ tiêu — chỉ cắt danh sách nguyện vọng của mọi em xuống k**,
50 seed mỗi mức.

| Cắt còn | Em **chưa được xếp** (TB) | Nhiều nhất | Em **bấp bênh** |
|---|---|---|---|
| 1 nguyện vọng | **48,0** | 48 | 2 (1,4%) |
| 2 nguyện vọng | 26,2 | 27 | 7 (5,0%) |
| 3 nguyện vọng | 14,8 | 16 | 3 (2,1%) |
| 4 nguyện vọng | 7,5 | 8 | 3 (2,1%) |
| 5 nguyện vọng | 1,2 | 3 | 4 (2,9%) |
| 6 nguyện vọng | **0,3** | 1 | 1 (0,7%) |

**Hai cột cuối kể hai câu chuyện khác nhau, đừng gộp:**

- **Chưa được xếp**: hiệu ứng rất mạnh và rất đều — **48 → 0,3**.
- **Bấp bênh**: **không có quy luật nào** — 1,4 / 5,0 / 2,1 / 2,1 / 2,9 / 0,7,
  nhảy loạn. Danh sách dài hơn **không** làm em bớt bấp bênh.

Phỏng đoán ban đầu **đúng mạnh** cho vế thứ nhất, **sai** cho vế thứ hai.

> **⚠️ Đừng đọc bảng này thành "bắt học sinh điền tối đa số CLB".** Thí nghiệm
> **CẮT BỚT** nguyện vọng của em vốn đã khai đủ, tức nó đo *"em mất gì khi không
> khai hết những CLB mình VẪN CHẤP NHẬN"*. Nó **không** đo chuyện thêm CLB em
> **không** muốn — mà thêm CLB không muốn thì em có thể bị xếp đúng vào đó, và
> với em như thế còn tệ hơn không có suất. Xem `BAN_GIAO.md` mục 5, khối "CẢNH
> BÁO DIỄN GIẢI".

```
python du_lieu_test/do_do_dai_nguyen_vong.py
```

Còn một điều nữa:

- **Mọi seed đều cho 0 cặp phá vỡ.** Đổi seed đổi *ai* được suất trong nhóm hoà
  nhau, chứ không bao giờ làm kết quả mất tính ổn định.

Trên `bo_sach/` thì 138/140 em có hoà điểm ở đâu đó và cả 140 em đều có ít nhất
một CLB mình không thi, nên câu "không em nào đổi ngoài hai nhóm" ở bộ này gần
như hiển nhiên. Bằng chứng mạnh nằm ở `vi_du_huong_dan/` và ở test dựng riêng
(`tests/test_anh_huong_seed.py`), nơi ba em ba điểm khác nhau tranh hai suất và
**100 seed đều cho cùng một kết quả**.

```
python du_lieu_test/do_anh_huong_seed.py --so-seed 200
```

Chạy hai lần ra **đúng cùng một bảng** — đã kiểm.

> Ba câu hỏi hay gặp về **bản thân phép bốc thăm** (đổi seed có còn công
> bằng không, thứ tự nhập có ảnh hưởng không, những gì ảnh hưởng tới bộ
> số) được trả lời riêng, kèm số đo, ở **`GIAI_DAP_BOC_THAM.md`**.

## 4. Kịch bản nhỏ kiểm được bằng tay

Xem `NHAP_TAY.md` — 8 học sinh, 3 CLB.

| Đại lượng | Giá trị |
|---|---|
| Được xếp | 6 / 8 |
| Em vào bằng suất dự trữ | 1 (điểm 6,0) |
| Em điểm cao hơn nhưng không vào CLB đó | 2 (điểm 8,5 và 8,0) |
| Số hạt giống đã thử | 5 (1, 7, 42, 999, 12345) |
| Số lần cho kết quả khác nhau | **0** |

Không có hai em bằng điểm trong cùng một CLB nên bước bốc thăm không được dùng
tới — kết quả tính được bằng tay.

## 5. Kiểm thử phần mềm

| Đại lượng | Giá trị |
|---|---|
| Tệp kiểm thử | 31 |
| Trường hợp kiểm thử | **404** |
| Số trường hợp không đạt | 0 |
| Thời gian chạy toàn bộ | ~95 giây |

## 6. Lỗi tìm được trong quá trình phát triển

| Đại lượng | Giá trị |
|---|---|
| Tổng số lỗi đã tìm và sửa | **25** |
| Trong đó là lỗi **im lặng** | **10** |

*Lỗi im lặng = phần mềm báo thành công trong khi dữ liệu đã sai.* Danh sách từng
lỗi và cách phát hiện nằm trong lịch sử Git và `BAN_GIAO.md` mục 5.

## 7. Chạy trên máy Windows thật

| Kiểm tra | Kết quả | Ngày |
|---|---|---|
| Mở được bản `.exe` | Có | 30/08 |
| Cửa sổ ứng dụng riêng, không thanh địa chỉ | Có | 30/08 |
| Mục riêng trên thanh tác vụ | Có | 30/08 |
| Còn sống sau 3–5 phút thu nhỏ | Có | 30/08 |
| Nạp 4 tệp Excel | Thành công | 30/08 |
| Số ứng viên mỗi CLB khớp với số đo trên máy phát triển | Khớp cả 10 | 30/08 |
| `PhanBoCauLacBo.exe` là tiến trình riêng trong Task Manager | Có | 31/08 |
| Cửa sổ gốc (pywebview) **được tạo** | Có | 31/08 |
| Cửa sổ gốc **dùng được** | **Chưa** — treo, xem dưới | 02/09 |

**Đã sửa lại một khẳng định sai ở mục này (02/09).** Bản trước ghi *"Cửa sổ gốc
(pywebview) mở được: Có"* và dẫn chứng bằng dòng nhật ký:

```
[2026-08-31 15:34:42] go dau tai-ve trong ...\_internal:
                      {'da_go': 173, 'bo_qua': 0, 'loi': 0}
[2026-08-31 15:34:42] cua so goc (pywebview) mo THANH CONG
```

**Dòng "mo THANH CONG" đó không chứng minh được điều nó có vẻ chứng minh.**
`main.py` ghi nó **trước** khi gọi `webview.start()` — mà `start()` mới là chỗ
thật sự mở cửa sổ, và cũng chính là chỗ đã treo. Nói cách khác, nhật ký ghi
"THÀNH CÔNG" ngay cả trong lần chạy mà app đứng hình. Chi tiết: `BAN_GIAO.md`
mục 5, lỗi 25.

Ngày 02/09 học sinh chạy thử: cửa sổ gốc **có** mở, nhưng tiêu đề ghi
**"(Not Responding)"** và giao diện không kết nối được với phần lõi. Nguyên nhân
đã tìm ra và đã sửa (`api.set_window` khiến pywebview đệ quy vào chính cửa sổ của
nó, chạm bốn property chặn 15 giây và đọc control WinForms chéo luồng).

**Trạng thái đúng tính đến 02/09:** bản vá đã có, đã đóng gói, **nhưng CHƯA được
xác nhận trên máy Windows.** Máy phát triển chạy Linux, không có .NET Framework
lẫn WinForms — cơ chế đo được bằng cách chạy lại đúng luật dò của pywebview
(`tests/test_do_api.py`), còn xác nhận cuối cùng phải do máy thật cho.

**Đường hiển thị được xác nhận là dùng được: chế độ dự phòng bằng trình duyệt**
(đã chạy trọn luồng nạp → chạy → xuất trên Windows ngày 30/08). Cửa sổ gốc là
đường ưu tiên trong mã, nhưng **báo cáo không được viết là nó đã chạy được** cho
tới khi có một lần chạy thành công trên máy Windows.

`da_go: 173` vẫn là số liệu đúng: đó là số tệp mang dấu "tải từ Internet" mà phần
mềm tự gỡ lúc khởi động. `bo_qua: 0` nghĩa là **không tệp nào sạch sẵn** — tức
việc gỡ dấu do **mã tự làm**, không phải người dùng thao tác tay.

---

*Phần diễn giải, nhận xét và đánh giá ý nghĩa của các con số trên, học sinh tự viết.*
