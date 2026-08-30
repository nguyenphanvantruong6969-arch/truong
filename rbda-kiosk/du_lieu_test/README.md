# Bộ dữ liệu chạy thử

> ### ⚠️ DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI HỌC SINH CÓ THẬT
>
> Toàn bộ tên và mã trong thư mục này do máy sinh ngẫu nhiên (seed cố định).
> Dùng để **chạy thử phần mềm**, không phải kết quả khảo sát. Trình bày các
> con số này như số liệu thật trong báo cáo là **bịa đặt dữ liệu**.

## Bốn file

| File | Nội dung | Dùng để |
|---|---|---|
| `TEST_01_danh_sach_CLB.xlsx` | 10 CLB, tổng 130 suất, 4 CLB có suất dự trữ | Nạp **đầu tiên** |
| `TEST_02_chon_CLB_muon_thi.xlsx` | 120 học sinh, mỗi em đăng ký thi 2–4 CLB | Nạp thứ hai |
| `TEST_03_xep_hang_nguyen_vong.xlsx` | Cùng 120 em, mỗi em 2–5 nguyện vọng | Nạp thứ ba |
| `TEST_04_CO_LOI_CO_Y.xlsx` | 10 dòng, cố ý sai 5 chỗ | Kiểm tra phần mềm **có cảnh báo không** |

Mỗi file có sheet **“Ghi chú”** giải thích nội dung ngay trong file.

## Hai đường thử khác nhau

- **Nạp tệp** — bốn tệp `.xlsx` ở trên, dùng ô kéo-thả. Đường mà nhà trường
  thật sự sẽ dùng khi có sẵn dữ liệu từ Microsoft Forms.
- **Gõ tay** — xem `NHAP_TAY.md`: 8 học sinh, 3 CLB, gõ trong ~15 phút. Kiểm tra
  các màn hình *Quản lý club*, *Nhập dự phòng tại kiosk*, *Chấm điểm* — những
  màn hình mà đường nạp tệp **không** đụng tới. Bộ này nhỏ đủ để tự tính kết quả
  bằng tay rồi đối chiếu với máy.

## Chạy thử bộ sạch

1. Kéo cả ba file `TEST_01`, `TEST_02`, `TEST_03` vào ô thả file — thứ tự nạp
   phần mềm tự sắp, không cần kéo đúng thứ tự.
2. Sang tab **Chấm điểm**, chấm cho từng CLB (điểm nào cũng được — đây là chạy thử).
3. Bấm **Chạy phân bổ**.
4. Bấm **Xuất kết quả**.

**Kết quả đúng phải ra như sau** (đã kiểm chứng bằng `seed=42`):

- 118/120 em được xếp, **2 em chưa được xếp** → có file `_chua_duoc_xep.csv`
- 11 file trong thư mục `ket_qua_phan_bo_theo_club/` (10 CLB + 1 file chưa xếp)
- CLB Âm nhạc, Khoa học, Mỹ thuật, Robotics, Tình nguyện, Văn học **đầy chỗ**;
  Bóng đá 17/20, Bóng rổ 16/18, Tiếng Anh 10/16, Tin học 11/12

Nếu máy bạn ra số khác, nhiều khả năng do bước chấm điểm (điểm khác thì thứ tự
xét khác) — đó là bình thường. Con số cần giống là **120 em, 10 CLB, không dòng
nào bị bỏ qua** ở bước nạp file.

## Chạy thử bộ có lỗi

Nạp `TEST_01` trước, rồi nạp `TEST_04`. Phần mềm **phải** hiện đủ **5 cảnh báo**:

| # | Lỗi cài sẵn | Cảnh báo phải hiện |
|---|---|---|
| 1 | `HS202` xuất hiện hai dòng | mã xuất hiện 2 lần, chỉ giữ dòng cuối |
| 2 | `hs201` vs `HS201` | đang coi là hai học sinh khác nhau |
| 3 | nhóm dự trữ `chinh_sac` (thiếu chữ h) | không CLB nào nhận, gợi ý `chinh_sach` |
| 4 | nguyện vọng vào `clb_khong_co` | club không tồn tại, bỏ qua học sinh này |
| 5 | mã `12348` giữa các mã 7 chữ số | nghi Excel đã cắt mất số 0 đầu |

**Thiếu bất kỳ cảnh báo nào là lỗi của phần mềm** — chụp màn hình và báo lại.

## Sinh lại

```bash
./.venv/bin/python du_lieu_test/tao_du_lieu_test.py
```

Seed cố định (`SEED = 2026`) nên chạy bao nhiêu lần cũng ra đúng bộ này.

*Phần nhận xét về kết quả chạy thử, học sinh tự viết.*
