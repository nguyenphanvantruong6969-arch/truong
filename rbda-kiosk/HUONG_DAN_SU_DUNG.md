# Hướng dẫn sử dụng — Phần mềm phân bổ câu lạc bộ (RB-DA Kiosk)

> Viết cho người **chưa từng mở phần mềm này**. Mỗi bước nói rõ: bấm vào đâu,
> sẽ thấy gì, và làm gì nếu không thấy như vậy.
>
> Tài liệu do AI soạn theo yêu cầu của học sinh, có ghi trong nhật ký AI.
> Đây là **tài liệu vận hành phần mềm**, không phải bài nghiên cứu.

---

## Mục lục

1. [Phần mềm này làm gì](#1-phần-mềm-này-làm-gì)
2. [Cần chuẩn bị gì](#2-cần-chuẩn-bị-gì)
3. [Mở phần mềm lần đầu](#3-mở-phần-mềm-lần-đầu)
4. [Nhìn quanh màn hình](#4-nhìn-quanh-màn-hình)
5. [Ba tệp Excel — từng cột nghĩa là gì](#5-ba-tệp-excel--từng-cột-nghĩa-là-gì)
6. [Chạy trọn quy trình — 5 bước](#6-chạy-trọn-quy-trình--5-bước)
7. [Đọc bảng kết quả](#7-đọc-bảng-kết-quả)
8. [Nhập tay tại kiosk](#8-nhập-tay-tại-kiosk)
9. [Làm lại từ đầu, và chuyện sao lưu](#9-làm-lại-từ-đầu-và-chuyện-sao-lưu)
10. [Bảng tra cảnh báo](#10-bảng-tra-cảnh-báo)
11. [Sự cố hay gặp](#11-sự-cố-hay-gặp)
12. [Thuật toán làm gì](#12-thuật-toán-làm-gì)
13. [Giới hạn đã biết](#13-giới-hạn-đã-biết)

---

## 1. Phần mềm này làm gì

Trường có nhiều câu lạc bộ, mỗi CLB có số chỗ giới hạn. Học sinh xếp hạng
nguyện vọng của mình. Phần mềm quyết định **ai vào CLB nào**.

Nó không quyết định bừa. Nó chạy một thuật toán có tên **RB-DA**, bảo đảm hai
điều: không có cặp học sinh–CLB nào mà **cả hai** đều muốn đổi cho nhau (gọi là
*kết quả ổn định*), và một số chỗ được **dành riêng** cho học sinh thuộc diện ưu
tiên do trường tự đặt.

Phần mềm chạy **hoàn toàn ngoại tuyến** trên một máy tính Windows. Không gửi dữ
liệu đi đâu, không cần Internet.

---

## 2. Cần chuẩn bị gì

| Cần | Ghi chú |
|---|---|
| Máy tính **Windows 10 hoặc 11** | Không cần cài đặt gì thêm |
| Thư mục phần mềm, trong đó có `PhanBoCauLacBo.exe` | Giải nén từ tệp `.zip` |
| **Ba tệp Excel** | Xem mục 5. Có sẵn bộ ví dụ để thử |
| Khoảng 15 phút cho lần đầu | |

**Bộ ví dụ để tập:** thư mục `du_lieu_test/vi_du_huong_dan/` — 10 học sinh, 4
CLB. Cả hướng dẫn này dùng đúng bộ đó, nên bạn làm theo tới đâu là đối chiếu
được tới đó.

> ⚠️ Mọi bộ dữ liệu đi kèm phần mềm đều là **DỮ LIỆU MÔ PHỎNG** — tên và điểm
> đều là bịa. Không được trình bày như số liệu khảo sát thật.

---

## 3. Mở phần mềm lần đầu

**Bước 1.** Chuột phải vào tệp **`.zip`** *(làm trước khi giải nén)* → **Properties**
→ cuối tab *General*, nếu có ô **Unblock** thì tích vào → **OK**.

Bỏ qua bước này thường vẫn chạy được — phần mềm tự xử lý. Nhưng làm thì chắc hơn.

**Bước 2.** Giải nén vào một thư mục, rồi bấm đúp `PhanBoCauLacBo.exe`.

**Bước 3.** Windows có thể hiện bảng xanh **"Windows protected your PC"**.

> Đây **không phải lỗi phần mềm**. Mọi ứng dụng không mua chứng chỉ ký số
> thương mại đều bị cảnh báo như vậy.

Bấm **More info** → **Run anyway**. Windows nhớ lựa chọn, nên chỉ hiện lần đầu
trên mỗi máy.

**Bước 4.** Cửa sổ phần mềm mở ra. Nhìn **góc dưới bên trái**: dòng cuối phải
ghi **"Cửa sổ ứng dụng riêng"**. Nếu ghi **"Chế độ dự phòng (trình duyệt)"** màu
vàng thì xem [mục 11](#11-sự-cố-hay-gặp).

---

## 4. Nhìn quanh màn hình

Bên trái là **thanh bên**, luôn hiện. Nó cho biết cơ sở dữ liệu đang kết nối,
lần chạy gần nhất là khi nào, và phần mềm đang vẽ cửa sổ bằng đường nào.

Trên cùng là **năm tab**:

| Tab | Dùng để |
|---|---|
| **01 · Vận hành pipeline** | Nạp tệp, xem cảnh báo, chạy phân bổ, xuất kết quả |
| **02 · Kết quả** | Xem ai vào CLB nào, mỗi CLB đầy đến đâu |
| **03 · Nhập dự phòng** | Gõ tay cho em không nộp được qua biểu mẫu |
| **04 · Quản lý club & dự trữ** | Thêm/sửa CLB, gán diện ưu tiên, xoá dữ liệu |
| **05 · Chấm điểm (mù)** | Giáo viên nhập điểm vòng thi |

**"Chấm điểm mù" nghĩa là gì:** màn hình chấm điểm **chỉ hiện mã và họ tên**. Nó
không hiện số bốc thăm, cũng không hiện em đó xếp CLB này là nguyện vọng thứ
mấy. Người chấm không biết cho điểm này thì ai được lợi.

---

## 5. Ba tệp Excel — từng cột nghĩa là gì

Phần mềm đọc thẳng `.xlsx`. Không cần tự chuyển sang CSV.

### Tệp 1 — Danh sách CLB

**Phải nạp trước hai tệp kia.** Nạp học sinh trước khi có CLB thì mọi học sinh bị
bỏ qua, vì mã CLB các em tham chiếu chưa tồn tại.

| Cột | Bắt buộc | Nghĩa |
|---|---|---|
| `club_id` | ✔ | Mã CLB, không dấu, không cách. Đây là thứ hai tệp kia tham chiếu tới |
| `name` | ✔ | Tên hiển thị, có dấu thoải mái |
| `capacity` | ✔ | **Tổng** số chỗ |
| `reserve_capacity` | | Trong tổng số đó, bao nhiêu chỗ **dành riêng** cho diện ưu tiên |
| `reserve_group` | | Nhãn diện ưu tiên. Bỏ trống nếu CLB không có suất dự trữ |

Bộ ví dụ:

| club_id | name | capacity | reserve_capacity | reserve_group |
|---|---|---|---|---|
| clb_bongro | CLB Bóng rổ | 3 | 1 | chinh_sach |
| clb_tinhoc | CLB Tin học | 2 | 0 | |
| clb_mythuat | CLB Mỹ thuật | 2 | 0 | |
| clb_nauan | CLB Nấu ăn | 3 | 0 | |

Đọc dòng đầu: Bóng rổ có **3 chỗ**, trong đó **1 chỗ** dành cho học sinh mang
nhãn `chinh_sach`. Hai chỗ còn lại cạnh tranh bình thường.

> **`reserve_capacity` nằm TRONG `capacity`, không cộng thêm.** Ghi 3 và 1 nghĩa
> là 3 chỗ tất cả, không phải 4.

### Tệp 2 — Chọn CLB muốn thi, kèm điểm

| Cột | Nghĩa |
|---|---|
| `student_id` | Mã học sinh |
| `name` | Họ tên |
| `reserve_group` | Nhãn diện ưu tiên của em này. Bỏ trống nếu không thuộc diện nào |
| `test_club_1`, `test_club_2`, … | Mã CLB em đăng ký thi |
| `score_1`, `score_2`, … | Điểm tương ứng |

> **`score_2` đi với `test_club_2`** — ghép theo **số** trong tên cột, không theo
> vị trí. Em bỏ trống `test_club_2` mà điền `test_club_3` thì vẫn ghép đúng.

Bộ ví dụ (3 dòng đầu):

| student_id | name | reserve_group | test_club_1 | score_1 | test_club_2 | score_2 |
|---|---|---|---|---|---|---|
| HS01 | Nguyễn Văn An | | clb_bongro | 9 | clb_tinhoc | 7.5 |
| HS02 | Trần Thị Bình | | clb_bongro | 8.5 | clb_mythuat | 8 |
| HS04 | Phạm Thu Dung | chinh_sach | clb_bongro | 6 | clb_mythuat | 6.5 |

Có sẵn điểm trong tệp thì **không phải gõ tay** ở tab Chấm điểm.

### Tệp 3 — Xếp hạng nguyện vọng

| Cột | Nghĩa |
|---|---|
| `student_id`, `name`, `reserve_group` | Như tệp 2 |
| `pref_1` | Nguyện vọng **mong muốn nhất** |
| `pref_2`, `pref_3`, … | Nguyện vọng tiếp theo |

Bộ ví dụ (3 dòng đầu):

| student_id | name | pref_1 | pref_2 |
|---|---|---|---|
| HS01 | Nguyễn Văn An | clb_bongro | clb_tinhoc |
| HS03 | Lê Minh Cường | clb_bongro | clb_nauan |
| HS10 | Dương Bá Minh | clb_bongro | *(để trống)* |

Ô trống là bình thường. Nhưng lưu ý HS10: em chỉ xếp **một** nguyện vọng, vào
đúng CLB đông nhất. Em này sẽ không có đường lui — xem [mục 7](#7-đọc-bảng-kết-quả).

### Ba quy tắc dễ sai nhất

1. **Mã CLB ở tệp 2 và 3 phải khớp `club_id` ở tệp 1.** Gõ sai một chữ là cả học
   sinh đó bị bỏ qua (có cảnh báo).
2. **Chỉ nên thi những CLB đã xếp nguyện vọng.** Thi một CLB mà không xếp nguyện
   vọng vào đó là lượt thi bỏ phí — dù điểm cao cũng không vào được.
3. **Mã học sinh phân biệt hoa/thường.** `HS01` và `hs01` là **hai** người khác
   nhau. Phần mềm cảnh báo khi thấy hai cách viết chỉ khác hoa/thường.

---

## 6. Chạy trọn quy trình — 5 bước

### Bước 1 — Nạp ba tệp

Tab **01 · Vận hành pipeline**. Kéo cả ba tệp `.xlsx` thả vào ô kéo-thả, hoặc
bấm vào ô đó để chọn tệp.

Thả cùng lúc cả ba cũng được — **phần mềm tự sắp thứ tự nạp**, CLB trước, học
sinh sau.

Mỗi tệp hiện một dòng, kèm chữ *"Nhận diện: …"* cho biết phần mềm hiểu đó là loại
tệp gì. **Đọc dòng này trước khi bấm nhập.** Nhận diện sai thì có ô chọn lại.

Bấm **Nhập tất cả**. Mỗi dòng đổi thành *"Xong: … "* kèm số liệu.

### Bước 2 — Đọc mục *Cảnh báo dữ liệu*

Ngay dưới ô nạp tệp. Đây là **bước quan trọng nhất và cũng là bước hay bị bỏ qua
nhất**.

Cảnh báo ở đây **không chặn** phần mềm chạy. Chúng là những thiếu sót vẫn để
thuật toán chạy trơn tru nhưng **âm thầm làm đổi kết quả**. Chạy mà không đọc thì
sẽ có kết quả — chỉ là không phải kết quả bạn tưởng.

Với bộ ví dụ, chỗ này phải ghi **0 cảnh báo**. Nếu có, tra [mục 10](#10-bảng-tra-cảnh-báo).

### Bước 3 — Chấm điểm *(bỏ qua nếu tệp đã có điểm)*

Tab **05 · Chấm điểm (mù)**. Chọn CLB, nhập điểm cho từng em, bấm lưu.

> Ô điểm nhận **cả hai cách viết**: `8,5` (kiểu Việt) và `8.5` đều lưu thành
> cùng một giá trị. Lưu xong màn hình hiện lại `8.5` — đó là cùng con số, không
> phải máy sửa gì.

Bộ ví dụ đã có sẵn điểm trong tệp 2, nên bước này bỏ qua.

### Bước 4 — Chạy phân bổ

Quay lại tab **01**. Bấm **Chạy phân bổ**.

Phần mềm hỏi lại một lần trước khi chạy — vì chạy lần hai sẽ **ghi đè** kết quả
lần trước. Bấm xác nhận.

Màn hình hiện tiến trình 5 bước: sao lưu → kiểm tra dữ liệu → bốc thăm → chạy
thuật toán → ghi kết quả.

> **Ô `seed`** là hạt giống bốc thăm, mặc định `42`. Cùng dữ liệu và cùng `seed`
> thì **luôn ra cùng kết quả** — kể cả trên máy khác, hệ điều hành khác, và
> **kể cả khi nhập học sinh theo thứ tự khác**. Đó là cách kiểm chứng lại kết quả
> sau này. Đừng đổi nếu không có lý do.
>
> Bốc thăm vẫn hoàn toàn ngẫu nhiên: mã học sinh **không** quyết định ai được số
> tốt. Em `HS01` không hề có lợi thế nào so với em cuối danh sách.

### Bước 5 — Xuất kết quả

Bấm **Xuất kết quả**. Phần mềm ghi ra hai thứ:

1. **Một tệp tổng** — toàn bộ học sinh, mỗi em một dòng.
2. **Một thư mục kèm theo**, tên là tên tệp tổng cộng thêm `_theo_club`. Trong đó:
   - mỗi CLB một tệp riêng, để in dán bảng tin
   - thêm tệp **`_chua_duoc_xep.csv`** — những em chưa được xếp vào đâu

Với bộ ví dụ, thư mục đó có 5 tệp: `clb_bongro.csv`, `clb_mythuat.csv`,
`clb_nauan.csv`, `clb_tinhoc.csv` và `_chua_duoc_xep.csv`.

Mọi tệp đều mở được bằng Excel, tiếng Việt không vỡ dấu.

> Tệp kết quả là **dữ liệu học sinh**. Cân nhắc trước khi gửi qua email hay chép
> lên máy dùng chung.

---

## 7. Đọc bảng kết quả

Tab **02 · Kết quả**, hoặc mở tệp vừa xuất.

| Cột | Nghĩa |
|---|---|
| Mã học sinh, Họ tên | |
| Mã CLB, Tên CLB | CLB em được xếp vào. **Trống = chưa được xếp** |
| **Nguyện vọng thứ** | Em vào CLB này là nguyện vọng thứ mấy của em. `1` là toại nguyện |
| **Diện trúng tuyển** | `Thường` = cạnh tranh ở chỉ tiêu chung · `Dự trữ` = vào bằng suất dành riêng |
| Nhóm dự trữ | Nhãn diện ưu tiên của em, nếu có |

### Kết quả đúng của bộ ví dụ

Chạy với `seed = 42`:

| Mã | Họ tên | CLB | NV thứ | Diện |
|---|---|---|---|---|
| HS01 | Nguyễn Văn An | CLB Bóng rổ | 1 | Thường |
| HS02 | Trần Thị Bình | CLB Bóng rổ | 1 | Thường |
| HS03 | Lê Minh Cường | CLB Nấu ăn | **2** | Thường |
| HS04 | Phạm Thu Dung | CLB Bóng rổ | 1 | **Dự trữ** |
| HS05 | Hoàng Văn Đức | CLB Tin học | **2** | Thường |
| HS06 | Vũ Ngọc Giang | CLB Tin học | 1 | Thường |
| HS07 | Đỗ Thị Hạnh | CLB Mỹ thuật | 1 | Thường |
| HS08 | Bùi Quang Khánh | CLB Mỹ thuật | 1 | Thường |
| HS09 | Ngô Phương Linh | CLB Nấu ăn | 1 | Thường |
| **HS10** | Dương Bá Minh | *(trống)* | — | — |

Sức chứa: Bóng rổ **3/3** · Mỹ thuật **2/2** · Tin học **2/2** · Nấu ăn **2/3**

Ở tab **02 · Kết quả** còn có biểu đồ *Tỉ lệ lấp đầy theo club*. Mỗi thanh đọc
như sau: phần **vàng** là số em vào **bằng suất dự trữ**, phần **xanh** là số em
vào ở chỉ tiêu chung, phần **trắng còn lại** là chỗ chưa lấp đầy. Hai phần màu
cộng lại đúng bằng con số in bên phải thanh.

**Ra khác bảng này là có gì đó đã đổi** — dữ liệu, `seed`, hoặc phiên bản phần mềm.

### Ba điều bảng này cho thấy

**HS03 và HS05 không được nguyện vọng 1.** Sáu em xếp Bóng rổ làm nguyện vọng 1
nhưng chỉ có 3 chỗ. Hai em này tụt xuống nguyện vọng 2.

**HS04 vào bằng suất dự trữ.** Em này điểm Bóng rổ **6,0** — thấp nhất trong số
em xếp Bóng rổ. Chạy thử lại sau khi bỏ suất dự trữ đi thì **đúng một chỗ đổi
chủ**:

| | Có suất dự trữ | Bỏ suất dự trữ |
|---|---|---|
| HS04 *(6,0 · diện chinh_sach)* | **CLB Bóng rổ** | **chưa được xếp** |
| HS03 *(8,0)* | CLB Nấu ăn | CLB Bóng rổ |

**HS10 chưa được xếp, dù Nấu ăn còn trống một chỗ.** Vì em chỉ xếp **một** nguyện
vọng, vào đúng CLB đông nhất. Thuật toán **không nhét học sinh vào CLB các em
không chọn** — nếu có, nó đã tự quyết thay các em.

> Gặp tệp `_chua_duoc_xep.csv` không có nghĩa là phần mềm hỏng. Nó có nghĩa là
> những em đó cần được hỏi lại nguyện vọng. **Cách phòng: khuyến khích học sinh
> xếp nhiều nguyện vọng.**

---

## 8. Nhập tay tại kiosk

Dùng khi học sinh không nộp được qua biểu mẫu.

Tab **03 · Nhập dự phòng**. Ba bước tách biệt, không ảnh hưởng lẫn nhau:

1. **Tìm hoặc tạo học sinh** — gõ mã hoặc tên. Chưa có thì bấm *Tạo học sinh mới*.
2. **Chọn CLB muốn thi** — tick vào các CLB em muốn thi.
3. **Xếp hạng nguyện vọng** — chọn theo thứ tự, `pref_1` là mong muốn nhất.

Có nút **Xoá học sinh** cho trường hợp tạo nhầm mã. Nút này **bị chặn** nếu em đó
đã nằm trong kết quả của lần chạy gần nhất — phải chạy lại pipeline trước.

---

## 9. Làm lại từ đầu, và chuyện sao lưu

### Nạp tệp chỉ CỘNG THÊM học sinh

Đây là điều dễ hiểu nhầm nhất. Nạp tệp **không xoá** học sinh đã có. Đó là hành
vi đúng — trường nạp khối 10 rồi nạp khối 11 thì không được mất khối 10.

Nhưng nghĩa là: **muốn chạy thử lại với bộ dữ liệu khác thì phải xoá trước**.
Không xoá thì học sinh của lần trước vẫn chiếm suất và làm lệch kết quả.

### Cách xoá

Tab **04 · Quản lý club & dự trữ**, kéo xuống cuối trang, khối **Vùng nguy hiểm**:

| Nút | Xoá gì |
|---|---|
| **Xoá toàn bộ học sinh (giữ CLB)** | Học sinh, nguyện vọng, điểm, kết quả — **giữ** danh sách CLB |
| **Xoá toàn bộ dữ liệu** | Như trên, và xoá cả danh sách CLB |

Phải bấm **hai lần** mới xoá thật. Bấm một lần chỉ đổi nhãn nút thành *"Bấm lần
nữa để…"*; không bấm tiếp trong 4 giây thì nút tự nhả.

### Không mất gì

Cả hai nút đều **tự sao lưu `app.db`** trước khi xoá. Tên tệp sao lưu hiện trong
thông báo, dạng `app.db.bak-20260901_132528`. Muốn lấy lại: đóng phần mềm, đổi
tên tệp đó thành `app.db`.

**Nhật ký các lần chạy không bao giờ bị xoá** — dấu vết kiểm toán được giữ nguyên.

### Sao lưu thường ngày

Toàn bộ dữ liệu nằm trong **một tệp duy nhất**: `app.db`, cạnh
`PhanBoCauLacBo.exe`. Sao lưu = đóng phần mềm rồi chép tệp đó ra USB. Không cần
chép tệp nào khác.

---

## 10. Bảng tra cảnh báo

Bảy quy tắc rà soát. Mỗi cảnh báo nói một điều **vẫn để phần mềm chạy** nhưng làm
đổi kết quả.

| Cảnh báo | Nghĩa là gì | Sửa ở đâu |
|---|---|---|
| **CLB … chưa chấm điểm ai** | Có em đăng ký thi nhưng chưa ai được chấm. Cả nhóm rơi xuống tầng 2, vòng thi coi như không có tác dụng | Tab 05 · Chấm điểm |
| **CLB … mới chấm x/y** | Em chưa có điểm bị xếp **dưới tất cả** em đã có điểm, kể cả em thấp nhất | Tab 05 · Chấm điểm |
| **n lượt thi bỏ phí** | Em đăng ký thi một CLB nhưng không xếp CLB đó vào nguyện vọng. Điểm cao mấy cũng không vào được | Sửa tệp 3, nạp lại |
| **n em chưa xếp nguyện vọng nào** | Những em này chắc chắn không được xếp vào đâu | Sửa tệp 3, hoặc tab 03 |
| **Nhãn dự trữ "…" không CLB nào dùng** | Gõ sai chính tả nhãn. Em mang nhãn đó **mất quyền ưu tiên ở mọi nơi**. Cảnh báo có kèm mã học sinh | Tab 04: tìm mã em, tick, để trống ô nhãn, bấm *Gán* |
| **CLB … có suất dự trữ nhưng chưa đặt nhãn** | Các suất đó âm thầm thành suất phổ thông | Tab 04: sửa CLB |
| **CLB … dành suất cho nhãn chưa em nào mang** | Suất dự trữ sẽ không dùng đến | Kiểm tra lại cột `reserve_group` ở tệp 2 hoặc 3 |
| **Tổng chỗ ít hơn số học sinh** | Chắc chắn có em không có chỗ. Đây là thông tin, không phải lỗi | Tăng chỉ tiêu, hoặc chấp nhận |
| **Club … có n điểm lệch hẳn** | Một điểm cách xa hẳn các điểm còn lại của chính CLB đó — thường là gõ `70` thay vì `7.0`. Điểm sai đẩy em đó lên đầu bảng và kéo em khác tụt xuống | Tab 05 · Chấm điểm |

Ngoài ra, **lúc nạp tệp** còn có cảnh báo riêng: mã trùng hoa/thường, một mã xuất
hiện hai dòng, mã nghi bị Excel cắt mất số 0 đứng đầu, mã CLB không tồn tại, cột
điểm đặt nhầm vào tệp nguyện vọng.

---

## 11. Sự cố hay gặp

### Màn hình ghi "Đang kết nối với phần lõi chương trình…"

Bình thường. Lần mở **đầu tiên sau khi cài** hay lâu hơn những lần sau, vì
Windows còn đang dựng bộ hiển thị và quét tệp mới. Cứ để yên, đừng bấm gì.

Nếu sau đó hiện câu **"Không kết nối được với phần lõi chương trình"**:

1. Đóng hẳn cửa sổ rồi mở lại phần mềm — phần lớn trường hợp hết ngay.
2. Vẫn vậy thì gửi tệp **`loi_khoi_dong.txt`** (nằm cùng thư mục với `app.db`)
   cho người phụ trách. Tệp đó ghi rõ phần mềm hỏng ở bước nào — không có nó thì
   chỉ còn cách đoán.

> Bản trước có lỗi ở chỗ này: đôi khi màn hình hiện câu tiếng Anh
> *"Backend not ready yet"*. Đã sửa. Nếu vẫn thấy câu tiếng Anh đó, nghĩa là bản
> `.exe` đang dùng là **bản cũ** — cần lấy bản mới.

### Mở tệp xuất ra bằng Excel thì vỡ dấu tiếng Việt

Không nên xảy ra — phần mềm ghi kèm dấu nhận dạng (BOM) để Excel hiểu đúng.
Nếu vẫn vỡ: trong Excel dùng **Data → From Text/CSV**, chọn mã hoá **UTF-8**.

### Phần mềm mở ra trong cửa sổ Edge

Nhìn góc dưới bên trái. Ghi **"Chế độ dự phòng (trình duyệt)"** màu vàng nghĩa là
cửa sổ gốc không mở được.

Nguyên nhân: Windows gắn dấu *"tải từ Internet"* vào tệp giải nén từ `.zip` tải
về. Bản mới **tự gỡ dấu** lúc khởi động nên hiếm khi gặp. Nếu gặp:

1. Chuột phải tệp `.zip` → **Properties** → tích **Unblock** → giải nén lại vào
   thư mục **mới**
2. Đã lỡ giải nén rồi thì mở PowerShell tại thư mục đó, gõ:
   `Get-ChildItem -Recurse | Unblock-File`
3. Vẫn không được thì mở tệp **`loi_khoi_dong.txt`** cạnh `PhanBoCauLacBo.exe` —
   trong đó có nguyên văn lý do.

> Chạy ở chế độ dự phòng **không thiếu tính năng nào**. Khác biệt duy nhất là máy
> phải có sẵn Edge hoặc Chrome.

### Nạp tệp xong mà số học sinh cao hơn mong đợi

Dữ liệu lần trước vẫn còn. Xem [mục 9](#9-làm-lại-từ-đầu-và-chuyện-sao-lưu).

### Lỡ xoá dữ liệu

Tệp `app.db.bak-…` nằm cạnh `PhanBoCauLacBo.exe`. Đóng phần mềm, đổi tên tệp đó
thành `app.db`.

### Excel làm mất số 0 đứng đầu mã học sinh

`0012345` để Excel tự nhận định dạng thì thành `12345`. Phần mềm **phát hiện
được** và cảnh báo, nhưng **không cứu được** — nó không biết mã gốc dài bao nhiêu.
Cách phòng: định dạng cột mã học sinh thành **Text** trước khi nhập liệu.

---

## 12. Thuật toán làm gì

Phần này mô tả **cách phần mềm hoạt động**, để người dùng hiểu vì sao kết quả ra
như vậy.

### Ý tưởng gốc: học sinh "nộp đơn" theo vòng

1. Mỗi em nộp đơn vào **nguyện vọng 1** của mình.
2. Mỗi CLB xếp hạng tất cả đơn nhận được, **giữ tạm** số em bằng đúng chỉ tiêu,
   từ chối phần còn lại.
3. Em bị từ chối nộp tiếp vào **nguyện vọng kế tiếp**.
4. Lặp lại cho tới khi không còn ai bị từ chối.

Điểm mấu chốt: CLB chỉ **giữ tạm**. Vòng sau có em giỏi hơn nộp vào thì em đang
được giữ bị đẩy ra, và lại đi nộp tiếp. Nhờ vậy không ai bị chốt sớm một cách bất
công. Bộ ví dụ chạy xong sau **2 vòng**.

### CLB xếp hạng đơn thế nào

Hai tầng:

- **Tầng 1** — em **có thi** CLB đó: xếp theo **điểm**, cao trước.
- **Tầng 2** — em **không thi** nhưng có xếp nguyện vọng: xếp theo **số bốc thăm**.

Tầng 1 luôn đứng trên tầng 2. Bằng điểm nhau thì **số bốc thăm** phân định.

### Số bốc thăm (STB)

Mỗi em được bốc **một số duy nhất**, dùng chung cho **mọi** CLB. Không phải mỗi
CLB bốc lại một lần.

Vì sao quan trọng: nếu mỗi CLB bốc riêng, một em xui có thể xui ở tất cả các CLB
cùng lúc. Bốc một lần dùng chung thì rủi ro trải đều hơn.

Số bốc thăm sinh từ ô `seed`. Cùng `seed` → cùng bộ số → cùng kết quả. Sau lần
chạy đầu, số bốc thăm bị **khoá** để lần chạy sau không vô tình bốc lại và làm
đổi kết quả đã công bố.

### Đổi `seed` thì kết quả đổi tới đâu

Câu hỏi tự nhiên: nếu bốc thăm khác đi thì kết quả khác tới mức nào? Đã **đo**,
chạy lại toàn bộ quy trình với **200 seed** trên ba bộ dữ liệu:

| Bộ dữ liệu | Số em **không bao giờ** đổi CLB | Em đổi CLB (trung bình / nhiều nhất) |
|---|---|---|
| Ví dụ hướng dẫn — 10 em / 4 CLB | **10 / 10 (100%)** | 0 / 0 |
| Bộ sạch — 140 em / 12 CLB | **127 / 140 (91%)** | 6,0 / 11 em |
| Bộ TEST — 120 em / 10 CLB | **116 / 120 (97%)** | 1,9 / 4 em |

Bộ ví dụ trong hướng dẫn này **không có em nào hoà điểm và không em nào dự tuyển
CLB mình không thi**, nên `seed` không có chỗ nào để chen vào: đổi seed kiểu gì
cũng ra **đúng một kết quả**. Đó là minh hoạ trực tiếp cho quy tắc ở trên — điểm
đứng trước, bốc thăm chỉ phân định khi điểm đã hoà.

Hai điều nữa đã đo:

- **Mọi seed đều cho kết quả ổn định** — không có cặp phá vỡ nào ở bất kỳ seed
  nào trong 200 seed. Đổi seed đổi *ai* được suất trong nhóm hoà nhau, chứ không
  làm kết quả sai.
- **Seed có thể đổi cả việc một em có suất hay không**, không chỉ đổi CLB. Đã
  đếm riêng: trên **270 em của cả ba bộ, đúng 3 em (1,1%)** rơi vào diện này —
  0 em ở bộ ví dụ, 1 em (0,7%) ở bộ sạch, 2 em (1,7%) ở bộ TEST. Còn lại thì
  hoặc luôn có suất, hoặc luôn không, bất kể seed.

**Ba em đó rơi vào diện bấp bênh trong trường hợp nào:** em bị từ chối hết các
nguyện vọng trên, rơi xuống **nguyện vọng cuối cùng còn với tới được**, và ở
đúng đó lại đứng ngay ranh giới chỉ tiêu trong một nhóm hoà nhau. Thua lượt bốc
thăm ở chỗ đó thì không còn nguyện vọng nào phía dưới để rơi tiếp.

Một em trong số đó chỉ đăng ký **2 nguyện vọng**, nên không có lưới nào đỡ. Số
liệu chi tiết từng em ở `du_lieu_test/SO_LIEU_DA_KIEM_CHUNG.md` mục 3c.

Tái lập: `python du_lieu_test/do_anh_huong_seed.py --so-seed 200`

### Suất dự trữ

Trong `capacity` chỗ của một CLB, `reserve_capacity` chỗ được xét **trước** và
**chỉ** dành cho em mang đúng `reserve_group` của CLB đó.

Trường **tự đặt** tiêu chí. Phần mềm chỉ so khớp nhãn giữa CLB và học sinh, không
cài sẵn bất kỳ chính sách nào.

Suất dự trữ là *mềm*: nếu không đủ em thuộc diện đó, chỗ thừa **chuyển thành chỗ
phổ thông** chứ không bỏ trống.

### "Kết quả ổn định" nghĩa là gì

Khi chạy xong, không tồn tại cặp (học sinh X, CLB Y) nào mà **cả hai** đều muốn
đổi: X thích Y hơn CLB đang được xếp, **và** Y cũng sẵn sàng nhận X thay cho một
em đang giữ chỗ.

Phần mềm **tự kiểm chứng** điều này sau mỗi lần chạy. Bộ ví dụ: **0 cặp chặn**.

---

## 13. Giới hạn đã biết

Ghi ra để người dùng biết trước, không phải để bào chữa.

| Giới hạn | Ảnh hưởng |
|---|---|
| **Tối đa 10 nguyện vọng mỗi em** | Em xếp từ 11 nguyện vọng trở lên sẽ bị **bỏ qua cả hồ sơ**, có cảnh báo. Trường có trên 10 CLB cần lưu ý |
| **Điểm bất thường chỉ được CẢNH BÁO, không bị chặn** | Phần mềm không đặt trần cứng (trường có thể chấm thang 100), mà so mỗi điểm với trung vị của chính CLB đó. Lệch quá 3 lần thì báo — bắt được cả `70` lẫn `0.85`. Nhưng một điểm sai *vừa phải*, ví dụ 9 thay vì 8, thì không cách nào phát hiện được |
| **Chưa có nút "Sao lưu ngay"** | Phần mềm tự sao lưu trước mỗi lần chạy và trước khi xoá. Sao lưu thường ngày vẫn phải chép tay tệp `app.db` |
| **Windows cảnh báo nhà phát hành không xác định** | Do chưa mua chứng chỉ ký số thương mại, không phải lỗi phần mềm |
| **Vài em có suất hay không phụ thuộc bốc thăm** | Đo trên 270 em của ba bộ dữ liệu: **3 em (1,1%)**. Đây không phải lỗi — xem ngay dưới |

### Vì sao có em phụ thuộc bốc thăm, và vì sao đó không phải lỗi

Khi hai em **bằng điểm nhau** ở cùng một CLB còn đúng một chỗ, phải có gì đó phân
định. Mọi cách khác đều **thiên vị có hệ thống**: xếp theo thứ tự nhập thì ai nộp
sớm luôn thắng; xếp theo mã học sinh thì em mã nhỏ luôn thắng — cùng một người
được lợi ở **mọi** CLB, năm này qua năm khác. Bốc thăm không thiên vị ai.

Đã đo và **không** xảy ra ba điều đáng lo:

| Nếu | Đo được |
|---|---|
| Bốc thăm lật ngược kết quả của em **điểm khác nhau** | **Không.** 3 em 3 điểm khác nhau, 100 seed, cùng một kết quả |
| Bốc thăm làm kết quả mất tính ổn định | **Không.** 0 cặp phá vỡ trên 200 seed, cả ba bộ |
| Bốc thăm thiên vị một em cụ thể | **Không.** Hai em hoà điểm tranh một suất: cả hai đều từng thắng |

**Chỗ thật sự cần giữ, và phần mềm đã giữ:** vì bốc thăm *có* đổi số phận của vài
em, việc bốc đi bốc lại rồi chọn kết quả vừa ý là rủi ro thật. Sau lần chạy đầu,
bộ số bốc thăm bị **khoá**; bốc lại phải bật cờ riêng, không thể lỡ tay; và **mỗi
lần chạy đều ghi thêm một dòng vào lịch sử** kèm `seed` và dấu "đã bốc lại" —
bảng đó **không bao giờ bị ghi đè**, kể cả khi xoá toàn bộ dữ liệu. Ai bốc lại để
dò seed đẹp sẽ để lại dấu vết không xoá được.

**Điều nhà trường nên làm — quan trọng hơn mọi thứ trên:** nói với học sinh rằng
**hãy xếp hết những CLB em thật sự chấp nhận vào**. Đã đo hẳn hoi — cùng bộ dữ
liệu 140 em, chỉ cắt ngắn danh sách nguyện vọng:

| Mỗi em xếp | Số em không có suất (trung bình) |
|---|---|
| 1 nguyện vọng | **48 em** |
| 2 nguyện vọng | 26 em |
| 3 nguyện vọng | 15 em |
| 4 nguyện vọng | 7,5 em |
| 5 nguyện vọng | 1,2 em |
| 6 nguyện vọng | **0,3 em** |

Bỏ trống nguyện vọng là tự bỏ cơ hội của chính mình.

> ### ⚠️ Nhưng KHÔNG được bắt học sinh điền cho đủ số ô
>
> Bảng trên đo chuyện **cắt bớt** nguyện vọng của em vốn đã khai đủ — tức nó cho
> thấy em **mất gì khi không khai hết những CLB mình vẫn chấp nhận**. Nó **không**
> nói rằng bắt em khai thêm CLB em **không muốn** thì tốt.
>
> Bắt khai thêm CLB không muốn thì em có thể **bị xếp đúng vào CLB đó**, và với
> em như thế còn tệ hơn không có suất. Trường cũng mất luôn dữ liệu về nguyện
> vọng thật.
>
> Cách nói đúng với học sinh: *"Em cứ xếp theo đúng thứ tự em muốn, và đừng bỏ
> sót CLB nào em sẵn sàng vào. Khai thật là có lợi nhất cho em."*
>
> Và **không có suất không phải lúc nào cũng là thất bại**: em chỉ muốn 2 CLB, cả
> hai đều hết chỗ, thì không có suất là câu trả lời trung thực.

Số liệu đầy đủ: `du_lieu_test/SO_LIEU_DA_KIEM_CHUNG.md` mục 3c.
Ba câu hỏi hay gặp nhất về bốc thăm, kèm số đo: **`GIAI_DAP_BOC_THAM.md`**.

---

*Tài liệu này hướng dẫn vận hành phần mềm. Mọi nhận xét, diễn giải và kết luận về
kết quả phân bổ do người sử dụng tự viết.*
