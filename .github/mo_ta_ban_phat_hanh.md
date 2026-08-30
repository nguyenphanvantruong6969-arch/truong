Phần mềm phân bổ học sinh vào Câu lạc bộ, dùng thuật toán Reserve-Based
Deferred Acceptance (RB-DA). Chạy hoàn toàn ngoại tuyến, không cần cài đặt.

## Cách dùng

1. Tải `PhanBoCauLacBo-windows.zip` ở mục Assets bên dưới
2. Giải nén (chuột phải → Extract All)
3. Chạy `PhanBoCauLacBo.exe`

## Windows sẽ cảnh báo — đó là bình thường

Lần chạy đầu trên **mỗi máy**, Windows hiện *"Windows protected your PC"* hoặc
*"Nhà phát hành không xác định"*. Bấm **More info** → **Run anyway**. Windows nhớ
lựa chọn, những lần sau chạy thẳng.

Đây không phải virus và không phải lỗi. Mọi ứng dụng không mua chữ ký số thương
mại đều bị cảnh báo như vậy. Chi tiết trong `HUONG_DAN_CAI_DAT.md` ở thư mục vừa
giải nén.

## Có sẵn trong gói

| Thư mục | Nội dung |
|---|---|
| `mau_csv/` | Tệp CSV và Excel mẫu, kèm hướng dẫn định dạng |
| `du_lieu_test/` | Bộ dữ liệu **mô phỏng** 120 học sinh / 10 CLB để chạy thử |
| `HUONG_DAN_CAI_DAT.md` | Xử lý cảnh báo chữ ký số |
| `ky_va_tin_cay.ps1` | Ký bằng chứng chỉ tự tạo (tuỳ chọn, cần quyền Administrator) |

> Dữ liệu trong `du_lieu_test/` là **dữ liệu mô phỏng do máy sinh**, không phải
> học sinh có thật.
