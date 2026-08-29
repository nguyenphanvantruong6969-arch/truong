# Hướng dẫn định dạng CSV nhập vào phần mềm

Tài liệu này mô tả **chính xác** định dạng file CSV mà phần mềm đọc được,
kèm 4 file mẫu chạy thử được ngay trong cùng thư mục.

> Mọi quy tắc trong tài liệu này đều được **khoá bằng test tự động**
> (`tests/test_csv_mau.py`). Nếu code đổi mà tài liệu không đổi, test đỏ.

---

## 1. Có hai loại file cần nhập

Phần mềm chia quy trình đăng ký làm hai bước tách biệt, mỗi bước một file:

| Bước | Loại file | Nội dung | Nhập ở màn hình |
|---|---|---|---|
| **Bước 1** | Chọn club muốn thi/xét | Học sinh **tick** những club muốn dự tuyển (không xếp thứ tự) | 01 Vận hành pipeline |
| **Bước 2** | Xếp hạng nguyện vọng | Học sinh **xếp thứ tự** club theo mức độ mong muốn | 01 Vận hành pipeline |

Hai file độc lập nhau. Nhập file nào trước cũng được.

---

## 2. Mỗi loại file có hai dạng — chọn dạng nào cũng được

Phần mềm **tự nhận diện** dạng file, bạn không phải chọn gì. Cùng một dữ
liệu, hai dạng cho ra **kết quả giống hệt nhau**.

- **Dạng rộng** — mỗi học sinh **một dòng**. Dễ nhìn, dễ sửa bằng Excel.
- **Dạng dài** — mỗi lựa chọn **một dòng**. Đây là dạng
  `06_ms_forms_transform.py` xuất ra.

Phần mềm nhận ra dạng rộng khi thấy cột tên bắt đầu bằng `pref_` hoặc
`test_club_`. Không thấy thì hiểu là dạng dài.

---

## 3. Bảng cột chi tiết

### 3.1. Chọn club muốn thi — dạng rộng
**File mẫu: `01_chon_club_thi_dang_rong.csv`**

| Cột | Bắt buộc | Ý nghĩa |
|---|---|---|
| `student_id` | ✅ | Mã học sinh. Là **khoá chính** — phải duy nhất, không đổi giữa hai file. |
| `name` | Không | Họ tên. Chỉ dùng khi **tạo mới** học sinh; học sinh đã có tên thì không bị ghi đè. |
| `test_club_1`, `test_club_2`, … | ✅ ít nhất một | `club_id` của club muốn dự tuyển. **Ô trống được bỏ qua**, không cần điền kín. |

```csv
student_id,name,test_club_1,test_club_2,test_club_3,test_club_4
HS001,Nguyen Van An,clb_bongro,clb_tienganh,clb_amnhac,
HS002,Tran Thi Binh,clb_tienganh,,,
```

Số cột `test_club_*` tuỳ bạn — thêm bao nhiêu cũng được.

### 3.2. Chọn club muốn thi — dạng dài
**File mẫu: `02_chon_club_thi_dang_dai.csv`**

| Cột | Bắt buộc | Ý nghĩa |
|---|---|---|
| `student_id` | ✅ | Mã học sinh, **lặp lại** ở mỗi dòng của cùng học sinh. |
| `name` | Không | Họ tên. |
| `club_id` | ✅ | Một club mỗi dòng. |

```csv
student_id,name,club_id
HS001,Nguyen Van An,clb_bongro
HS001,Nguyen Van An,clb_tienganh
HS002,Tran Thi Binh,clb_tienganh
```

### 3.3. Xếp hạng nguyện vọng — dạng rộng
**File mẫu: `03_nguyen_vong_dang_rong.csv`**

| Cột | Bắt buộc | Ý nghĩa |
|---|---|---|
| `student_id` | ✅ | Mã học sinh. |
| `name` | Không | Họ tên. |
| `pref_1`, `pref_2`, … `pref_10` | ✅ ít nhất một | **Thứ tự cột chính là thứ tự nguyện vọng.** `pref_1` = nguyện vọng 1. |

```csv
student_id,name,pref_1,pref_2,pref_3
HS001,Nguyen Van An,clb_bongro,clb_amnhac,clb_tienganh
HS002,Tran Thi Binh,clb_tienganh,,
```

### 3.4. Xếp hạng nguyện vọng — dạng dài
**File mẫu: `04_nguyen_vong_dang_dai.csv`**

| Cột | Bắt buộc | Ý nghĩa |
|---|---|---|
| `student_id` | ✅ | Mã học sinh, lặp lại mỗi dòng. |
| `name` | Không | Họ tên. |
| `club_id` | ✅ | Một club mỗi dòng. |
| `rank` | Nên có | Thứ hạng nguyện vọng (1 = cao nhất). **Cột này quyết định thứ tự, không phải thứ tự dòng trong file.** Thiếu cột `rank` thì phần mềm mới dùng thứ tự dòng. |

```csv
student_id,name,club_id,rank
HS001,Nguyen Van An,clb_bongro,1
HS001,Nguyen Van An,clb_amnhac,2
```

---

## 4. Quy tắc phải biết trước khi nhập

### ⚠️ Tạo club TRƯỚC khi nhập
`club_id` trong file **phải đã tồn tại** trong phần mềm (màn hình
**04 Quản lý club & dự trữ**). Nếu một học sinh có bất kỳ `club_id` nào
sai, **cả học sinh đó bị bỏ qua** — phần mềm không nhập một nửa. Có cảnh
báo ghi rõ mã nào sai.

Đây là lỗi hay gặp nhất. Hãy dùng nút **Xem trước** rồi đọc số
"sẽ bị bỏ qua" trước khi bấm nhập thật.

### Nhập lại là GHI ĐÈ, không cộng dồn
Nhập lần hai **xoá sạch** nguyện vọng cũ của những học sinh có trong file,
rồi ghi lại từ đầu. Học sinh **không có** trong file thì không bị đụng tới.
Nhờ vậy bạn sửa một lớp mà không ảnh hưởng lớp khác.

### Tối đa 10 nguyện vọng
Giới hạn tính **sau khi loại trùng**. Học sinh có quá 10 nguyện vọng bị
**bỏ qua toàn bộ** — phần mềm không tự cắt còn 10, vì cắt bớt là âm thầm
đổi nguyện vọng của học sinh.

### Club trùng nhau được tự loại
Cùng một club xuất hiện nhiều lần thì chỉ giữ **lần đầu tiên**, kèm cảnh báo.

### Học sinh chưa có sẽ được tạo tự động
Mã học sinh chưa tồn tại thì phần mềm tạo mới, lấy `name` làm tên (không
có `name` thì lấy chính mã học sinh).

### ❗ CSV KHÔNG gán được nhóm dự trữ
Học sinh tạo bằng CSV có `reserve_group` **rỗng**. Mà nhóm dự trữ chính là
cơ chế ưu tiên của thuật toán RB-DA — **quên bước này thì toàn bộ phần dự
trữ không có tác dụng**, pipeline vẫn chạy bình thường và không báo lỗi.

Sau khi nhập CSV, vào màn hình **04 Quản lý club & dự trữ** để gán nhóm
(có chức năng gán hàng loạt cho nhiều học sinh cùng lúc).

---

## 5. Về file Excel

### Lưu file đúng cách
Trong Excel: **File → Save As → chọn `CSV UTF-8 (Comma delimited) (*.csv)`**.

Phải chọn đúng **UTF-8**, nếu không tên tiếng Việt có dấu sẽ thành ký tự
lạ trong phần mềm.

### Dấu phân cách
Phần mềm tự nhận cả **dấu phẩy `,`**, **dấu chấm phẩy `;`** và **Tab**.
Excel bản tiếng Việt hay lưu bằng dấu chấm phẩy — vẫn nhập được bình thường.

### Ký tự BOM
Excel thêm một ký tự vô hình (BOM) vào đầu file khi lưu CSV UTF-8.
Phần mềm **đã xử lý**, bạn không cần làm gì. (Trước phiên bản này, chính
ký tự đó khiến file đúng vẫn báo "thiếu cột `student_id`".)

---

## 6. Bảng lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Báo thiếu cột `student_id` | Sai tên cột, hoặc file có dòng tiêu đề phụ ở trên | Dòng đầu tiên phải là dòng tên cột |
| Nhiều học sinh "bị bỏ qua" | `club_id` chưa được tạo trong phần mềm | Kiểm tra lại danh sách club ở màn hình 04 |
| Tên tiếng Việt thành ký tự lạ | Lưu sai bảng mã | Lưu lại bằng **CSV UTF-8** |
| Nguyện vọng sai thứ tự | Dạng dài thiếu cột `rank` | Bổ sung cột `rank`, hoặc sắp đúng thứ tự dòng |
| Nhập xong nhưng dự trữ không chạy | Chưa gán `reserve_group` | Xem mục 4, phần ❗ |

---

## 7. Bộ club dùng trong file mẫu

Muốn chạy thử 4 file mẫu, tạo trước 5 club sau (màn hình 04):

| club_id | Tên | Chỉ tiêu | Chỉ tiêu dự trữ | Nhóm dự trữ |
|---|---|---|---|---|
| `clb_bongro` | CLB Bóng rổ | 20 | 0 | |
| `clb_tienganh` | CLB Tiếng Anh | 25 | 5 | `chinh_sach` |
| `clb_robotics` | CLB Robotics | 15 | 0 | |
| `clb_amnhac` | CLB Âm nhạc | 20 | 0 | |
| `clb_mythuat` | CLB Mỹ thuật | 18 | 3 | `chinh_sach` |

Dữ liệu trong file mẫu là **dữ liệu bịa để minh hoạ định dạng** — không
phải học sinh thật, không dùng làm số liệu nghiên cứu.
