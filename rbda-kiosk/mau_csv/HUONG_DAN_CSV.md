# Hướng dẫn định dạng CSV nhập vào phần mềm

Tài liệu này mô tả **chính xác** định dạng file CSV mà phần mềm đọc được,
kèm 4 file mẫu chạy thử được ngay trong cùng thư mục.

> Mọi quy tắc trong tài liệu này đều được **khoá bằng test tự động**
> (`tests/test_csv_mau.py`). Nếu code đổi mà tài liệu không đổi, test đỏ.

---

## 0. Cách nhập: kéo thả file Excel hoặc CSV

**Không cần chuyển file sang CSV nữa.** Phần mềm đọc thẳng `.xlsx` — đúng
định dạng Microsoft Forms xuất ra. Trước đây phải mở Excel → *Save As* →
chọn đúng *CSV UTF-8*; chính bước đó hay làm hỏng dấu tiếng Việt.

### File mẫu Excel — điền rồi thả vào là xong

| File | Dùng cho |
|---|---|
| `MAU_01_danh_sach_CLB.xlsx` | Danh sách CLB (nhập **trước tiên**) |
| `MAU_02_chon_CLB_muon_thi.xlsx` | Bước 1 — tick chọn CLB muốn dự tuyển |
| `MAU_03_xep_hang_nguyen_vong.xlsx` | Bước 2 — xếp thứ tự nguyện vọng |

Mỗi file có **hai sheet**: sheet đầu là bảng dữ liệu để điền, sheet sau là
hướng dẫn từng cột. Phần mềm **chỉ đọc sheet đầu**, nên ghi chú không bao giờ
lẫn vào dữ liệu. Cứ xoá 5 dòng mẫu rồi điền dữ liệu thật của trường.

Trộn định dạng cũng được: file này `.xlsx`, file kia `.csv` — thả chung một
lượt vẫn chạy.

## 0b. Không phải chọn loại file

Ở màn hình **01 Vận hành pipeline**, kéo file vào ô lớn — hoặc bấm vào ô đó
để chọn. **Không phải chọn loại file:** phần mềm đọc dòng tiêu đề là biết đây
là danh sách CLB, file chọn CLB muốn thi, hay file xếp hạng nguyện vọng.

Thả được **nhiều file một lúc**. Phần mềm tự nhập theo **đúng thứ tự**: danh
sách CLB trước, rồi mới đến file học sinh — vì học sinh tham chiếu tới
`club_id`, nạp ngược thứ tự thì cả học sinh bị bỏ qua.

Khi dòng tiêu đề **không đủ để kết luận**, phần mềm nói thẳng là chưa chắc và
hiện ô cho bạn chọn — nó không bao giờ tự đoán. Trường hợp này xảy ra với bộ
cột `student_id, name, club_id`: đúng bộ cột đó vừa có thể là "chọn CLB muốn
thi" dạng dài, vừa có thể là "xếp hạng nguyện vọng" dạng dài thiếu cột `rank`.

> Muốn phần mềm nhận ra chắc chắn ngay: thêm cột `rank` nếu là nguyện vọng,
> hoặc dùng dạng rộng (`pref_1…` / `test_club_1…`).

---

## 1. Có ba loại file nhập được

Phần mềm chia quy trình đăng ký làm hai bước tách biệt, mỗi bước một file:

| Thứ tự | Loại file | Nội dung |
|---|---|---|
| **Trước tiên** | Danh sách CLB | Mã CLB, tên, chỉ tiêu, chỉ tiêu dự trữ |
| **Bước 1** | Chọn club muốn thi/xét | Học sinh **tick** những club muốn dự tuyển (không xếp thứ tự) |
| **Bước 2** | Xếp hạng nguyện vọng | Học sinh **xếp thứ tự** club theo mức độ mong muốn |

Hai file học sinh độc lập nhau, nhập file nào trước cũng được — nhưng **danh
sách CLB phải có trước cả hai**.

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
| `reserve_group` | Không | **Nhóm dự trữ của học sinh** (vd `chinh_sach`). Xem mục 4. |
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
| `reserve_group` | Không | **Nhóm dự trữ của học sinh** (vd `chinh_sach`). Xem mục 4. |
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

### 3.5. Danh sách CLB
**File mẫu: `05_danh_sach_club.csv`**

| Cột | Bắt buộc | Ý nghĩa |
|---|---|---|
| `club_id` | ✅ | Mã CLB. Chính là mã dùng trong hai file học sinh — phải khớp từng ký tự. |
| `name` | ✅ | Tên đầy đủ để hiển thị và in ra file kết quả. |
| `capacity` | ✅ | Tổng chỉ tiêu. Phải **lớn hơn 0**. |
| `reserve_capacity` | Không | Số suất dành cho nhóm dự trữ. Bỏ trống = 0. Không được lớn hơn `capacity`. |
| `reserve_group` | Không | Tên nhóm được ưu tiên (vd `chinh_sach`). Bỏ trống = CLB không có dự trữ. |

```csv
club_id,name,capacity,reserve_capacity,reserve_group
clb_bongro,CLB Bóng rổ,20,0,
clb_tienganh,CLB Tiếng Anh,25,5,chinh_sach
```

Nhập lại file này là **cập nhật** CLB đã có (theo `club_id`), không tạo trùng.
Dòng nào có chỉ tiêu sai (bằng 0, hoặc dự trữ lớn hơn tổng chỉ tiêu) thì
**bỏ qua riêng dòng đó** kèm cảnh báo ghi rõ số dòng — các dòng còn lại vẫn
nhập bình thường.

---

## 4. Quy tắc phải biết trước khi nhập

### ⚠️ CLB phải có TRƯỚC file học sinh
`club_id` trong file học sinh **phải đã tồn tại**. Nếu một học sinh có bất kỳ
`club_id` nào chưa có, **cả học sinh đó bị bỏ qua** — phần mềm không nhập một
nửa. Có cảnh báo ghi rõ mã nào sai.

Cách chắc chắn nhất: thả **cả ba file cùng lúc** rồi bấm *Nhập tất cả*. Phần
mềm tự nhập danh sách CLB trước, nên không bao giờ rơi vào tình huống này.

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

### Nhóm dự trữ điền thẳng trong file
Thêm cột `reserve_group` vào file học sinh là xong — không phải vào màn hình
04 gán tay từng em nữa.

| Ô | Kết quả |
|---|---|
| Có giá trị | **Ghi đè** nhóm hiện có (người nhập chủ động đưa vào) |
| Để trống | **Giữ nguyên**, không xoá nhóm đã gán trước đó |
| Không có cột này | Cũng giữ nguyên — file thiếu cột không làm mất dữ liệu |

### Không phải lo gõ khác kiểu

Phần mềm **tự quy mọi cách viết về một mã**: bỏ dấu tiếng Việt, chuyển chữ
thường, thay khoảng trắng và dấu nối bằng gạch dưới.

| Bạn gõ | Phần mềm lưu |
|---|---|
| `chinh_sach` | `chinh_sach` |
| `Chính sách` | `chinh_sach` |
| `CHÍNH SÁCH` | `chinh_sach` |
| `Chính-Sách` | `chinh_sach` |
| `Đội tuyển` | `doi_tuyen` |
| `Khối 10` | `khoi_10` |

Nên file CLB ghi `chinh_sach` còn file học sinh gõ `Chính sách` vẫn nhận
nhau. Trước đây đó là hai nhóm khác nhau và học sinh diện chính sách **mất
suất dự trữ** mà không ai biết.

Chuẩn hoá chỉ gộp các cách viết **cùng một chữ**. `Khối 10` và `Khối 11` vẫn
là hai nhóm khác nhau, đúng như phải thế.

### Gõ sai hẳn thì được báo ngay

Nếu nhãn không CLB nào nhận — ví dụ gõ thiếu chữ thành `chinh_sac` — phần mềm
báo **ngay khi vừa nạp file**, kèm gợi ý:

> Nhãn dự trữ `chinh_sac` (1 học sinh) không CLB nào nhận — các em này sẽ
> KHÔNG được xét diện dự trữ. Có phải bạn định ghi `chinh_sach`?

Không phải chờ mở mục *Cảnh báo dữ liệu* mới thấy.

> Nhóm dự trữ chính là cơ chế ưu tiên của RB-DA. Bỏ trống hết thì thuật toán
> vẫn chạy trơn tru và **không báo lỗi gì** — chỉ là không em nào vào được
> theo diện dự trữ. Kiểm tra lại ở màn hình *04 Quản lý club & dự trữ*.

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
| Nhập xong nhưng dự trữ không chạy | Chưa điền `reserve_group`, hoặc gõ sai hẳn tên nhóm | Đọc cảnh báo hiện ngay sau khi nhập — nó gợi ý đúng nhóm bạn định ghi |
| Nhãn hiện ra khác lúc gõ (`Chính sách` thành `chinh_sach`) | Đúng thiết kế — phần mềm quy về một mã để hai file luôn khớp | Không phải sửa gì |
| Chỉ tiêu CLB từ Excel bị bỏ qua | (đã xử lý) Excel lưu số dạng `20.0`; phần mềm tự đưa về `20` |
| Phần mềm hỏi "chưa chắc đây là file gì" | Bộ cột hợp với cả hai loại | Chọn loại ở ô bên phải, hoặc thêm cột `rank` nếu là nguyện vọng |
| Học sinh bị bỏ qua hàng loạt ngay lần nhập đầu | Chưa nhập danh sách CLB | Thả cả file CLB vào cùng lúc, phần mềm tự xếp thứ tự |

---

## 7. Bộ club dùng trong file mẫu

Không phải tạo tay nữa — **thả `05_danh_sach_club.csv` vào cùng lúc** là xong.
Nội dung file đó đúng bằng bảng dưới:

| club_id | Tên | Chỉ tiêu | Chỉ tiêu dự trữ | Nhóm dự trữ |
|---|---|---|---|---|
| `clb_bongro` | CLB Bóng rổ | 20 | 0 | |
| `clb_tienganh` | CLB Tiếng Anh | 25 | 5 | `chinh_sach` |
| `clb_robotics` | CLB Robotics | 15 | 0 | |
| `clb_amnhac` | CLB Âm nhạc | 20 | 0 | |
| `clb_mythuat` | CLB Mỹ thuật | 18 | 3 | `chinh_sach` |

Dữ liệu trong file mẫu là **dữ liệu bịa để minh hoạ định dạng** — không
phải học sinh thật, không dùng làm số liệu nghiên cứu.
