# Số liệu đã kiểm chứng

> ### ⚠️ TOÀN BỘ SỐ Ở ĐÂY ĐO TRÊN **DỮ LIỆU MÔ PHỎNG**
> 120 học sinh do máy sinh (`tao_du_lieu_test.py`, seed 2026), **không phải khảo
> sát học sinh có thật**. Trình bày như số liệu thật là bịa đặt dữ liệu.

Đây là **số đo thô**, kèm cách đo lại. Phần nhận xét, giải thích ý nghĩa và kết
luận — **học sinh tự viết**, AI không tham gia.

Tái lập mọi số dưới đây:

```bash
./.venv/bin/python du_lieu_test/tao_db_demo.py     # dựng lại CSDL, seed 2026
./.venv/bin/python -m pytest -q                    # chạy bộ kiểm thử
```

---

## 1. Quy mô bài toán

| Đại lượng | Giá trị |
|---|---|
| Học sinh | 120 |
| Câu lạc bộ | 10 |
| Tổng chỉ tiêu | 130 chỗ |
| Trong đó là suất dự trữ | 12 chỗ (ở 4 CLB) |
| Lượt đăng ký thi | 356 |
| Học sinh thuộc diện dự trữ | 26 em — `chinh_sach` 19, `khoi_10` 7 |
| Học sinh không thuộc diện nào | 94 em |

## 2. Kết quả phân bổ

Chạy với `seed = 42`, điểm sinh từ seed 2026.

| Đại lượng | Giá trị |
|---|---|
| Được xếp | **118 / 120** |
| Chưa được xếp | 2 |
| Số vòng lặp thuật toán | 6 |
| Thời gian chạy | **0,012 giây** (cả 5 bước, gồm sao lưu và xuất tệp) |
| Tổng chỗ được dùng | 118 / 130 |

### Được xếp theo nguyện vọng thứ mấy

| Nguyện vọng | Số em |
|---|---|
| Thứ 1 | **93** |
| Thứ 2 | 19 |
| Thứ 3 | 6 |

### Diện trúng tuyển

| Diện | Số em |
|---|---|
| Thường (`general`) | 116 |
| Dự trữ (`reserve`) | **2** |

*(26 em thuộc diện dự trữ, nhưng chỉ 2 em thực sự cần dùng tới suất dự trữ để có
chỗ — số còn lại vào được bằng điểm thường.)*

### Lấp đầy từng CLB

| Mã CLB | Đã xếp / Chỉ tiêu | Suất dự trữ |
|---|---|---|
| `clb_amnhac` | 13 / 14 | 0 |
| `clb_bongda` | 14 / 20 | 0 |
| `clb_bongro` | 17 / 18 | 0 |
| `clb_khoahoc` | 8 / 8 | 2 |
| `clb_mythuat` | 12 / 12 | 3 |
| `clb_robotics` | 8 / 8 | 0 |
| `clb_tienganh` | 12 / 16 | 4 |
| `clb_tinhnguyen` | 12 / 12 | 0 |
| `clb_tinhoc` | 12 / 12 | 3 |
| `clb_vanhoc` | 10 / 10 | 0 |

Tệp xuất ra: **120 dòng** trong tệp tổng, **11 tệp** theo CLB (10 CLB + 1 tệp
`_chua_duoc_xep.csv`).

## 3. Tốc độ ở quy mô lớn hơn

Dữ liệu sinh ngẫu nhiên, đo trên cùng một máy:

| Quy mô | Nạp dữ liệu | Chạy phân bổ | Kết quả | Số vòng |
|---|---|---|---|---|
| 120 học sinh / 10 CLB | — | 0,012 s | 118/120 | 6 |
| 500 học sinh / 20 CLB | 0,03 s | 0,03 s | 500/500 | 21 |
| 2 000 học sinh / 40 CLB | 0,10 s | 0,13 s | 1 994/2 000 | 33 |

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
| Tệp kiểm thử | 15 |
| Trường hợp kiểm thử | **234** |
| Số trường hợp không đạt | 0 |
| Thời gian chạy toàn bộ | ~16 giây |

## 6. Lỗi tìm được trong quá trình phát triển

| Đại lượng | Giá trị |
|---|---|
| Tổng số lỗi đã tìm và sửa | **10** |
| Trong đó là lỗi **im lặng** | **7** |

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
