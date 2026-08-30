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
| Tệp kiểm thử | 18 |
| Trường hợp kiểm thử | **271** |
| Số trường hợp không đạt | 0 |
| Thời gian chạy toàn bộ | ~30 giây |

## 6. Lỗi tìm được trong quá trình phát triển

| Đại lượng | Giá trị |
|---|---|
| Tổng số lỗi đã tìm và sửa | **13** |
| Trong đó là lỗi **im lặng** | **10** |

*Lỗi im lặng = phần mềm báo thành công trong khi dữ liệu đã sai.* Danh sách từng
lỗi và cách phát hiện nằm trong lịch sử Git và `BAN_GIAO.md` mục 5.

## 7. Chạy trên máy Windows thật (30/08/2026)

| Kiểm tra | Kết quả |
|---|---|
| Mở được bản `.exe` | Có |
| Cửa sổ ứng dụng riêng (không thanh địa chỉ, không thanh tab) | Có |
| Mục riêng trên thanh tác vụ | Có |
| Còn sống sau 3–5 phút thu nhỏ | Có |
| Nạp 4 tệp Excel | Thành công |
| Số ứng viên mỗi CLB khớp với số đo trên máy phát triển | Khớp cả 10 |

**Đường hiển thị đang dùng:** chế độ dự phòng bằng nhân Chromium (xác nhận qua
Task Manager: tiến trình `msedge.exe`, cửa sổ mang tên *"Phân bổ Câu lạc bộ"*),
**không phải** pywebview. Xem `BAN_GIAO.md` mục 5.

---

*Phần diễn giải, nhận xét và đánh giá ý nghĩa của các con số trên, học sinh tự viết.*
